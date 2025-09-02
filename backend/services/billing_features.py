"""
Billing Features Service for MINGUS
Handles automatic invoice generation, email delivery, dunning management, tax calculation, and currency handling
"""
import stripe
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
import requests

from ..models.subscription import (
    Customer, Subscription, BillingHistory, PricingTier,
    AuditLog, AuditEventType, AuditSeverity
)
from ..config.base import Config
from .resend_email_service import resend_email_service

logger = logging.getLogger(__name__)

class BillingFeaturesError(Exception):
    """Custom exception for billing features errors"""
    pass

class BillingFeatures:
    """Comprehensive billing features for MINGUS"""
    
    def __init__(self, db_session: Session, config):
        self.db = db_session
        self.config = config
        self.stripe = stripe
        
        # Handle both object and dictionary configs
        if hasattr(config, 'STRIPE_SECRET_KEY'):
            self.stripe.api_key = config.STRIPE_SECRET_KEY
        elif isinstance(config, dict) and 'STRIPE_SECRET_KEY' in config:
            self.stripe.api_key = config['STRIPE_SECRET_KEY']
        else:
            self.stripe.api_key = None
        
        # Email configuration
        self.smtp_host = getattr(config, 'SMTP_HOST', 'smtp.gmail.com') if hasattr(config, 'SMTP_HOST') else config.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(config, 'SMTP_PORT', 587) if hasattr(config, 'SMTP_PORT') else config.get('SMTP_PORT', 587)
        self.smtp_username = getattr(config, 'SMTP_USERNAME', '') if hasattr(config, 'SMTP_USERNAME') else config.get('SMTP_USERNAME', '')
        self.smtp_password = getattr(config, 'SMTP_PASSWORD', '') if hasattr(config, 'SMTP_PASSWORD') else config.get('SMTP_PASSWORD', '')
        self.from_email = getattr(config, 'FROM_EMAIL', 'billing@mingus.com') if hasattr(config, 'FROM_EMAIL') else config.get('FROM_EMAIL', 'billing@mingus.com')
        
        # Tax service configuration
        self.tax_service_url = getattr(config, 'TAX_SERVICE_URL', '') if hasattr(config, 'TAX_SERVICE_URL') else config.get('TAX_SERVICE_URL', '')
        self.tax_service_api_key = getattr(config, 'TAX_SERVICE_API_KEY', '') if hasattr(config, 'TAX_SERVICE_API_KEY') else config.get('TAX_SERVICE_API_KEY', '')
        
        # Currency configuration
        self.default_currency = 'USD'
        self.supported_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
        self.exchange_rate_api_url = getattr(config, 'EXCHANGE_RATE_API_URL', '') if hasattr(config, 'EXCHANGE_RATE_API_URL') else config.get('EXCHANGE_RATE_API_URL', '')
    
    # ============================================================================
    # AUTOMATIC INVOICE GENERATION
    # ============================================================================
    
    def generate_automatic_invoice(
        self,
        subscription_id: int,
        invoice_type: str = 'recurring',
        custom_amount: float = None,
        description: str = None
    ) -> Dict[str, Any]:
        """Generate automatic invoice for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise BillingFeaturesError("Subscription not found")
            
            # Calculate invoice amount
            if custom_amount:
                amount = custom_amount
            else:
                amount = self._calculate_invoice_amount(subscription)
            
            # Generate invoice number
            invoice_number = self._generate_invoice_number(subscription.customer_id)
            
            # Create invoice record
            invoice = BillingHistory(
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                stripe_invoice_id=f"inv_{invoice_number}",
                invoice_number=invoice_number,
                amount_due=amount,
                amount_paid=0,
                currency=subscription.currency,
                status='pending',
                paid=False,
                invoice_date=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=7),
                invoice_type=invoice_type,
                description=description or f"{invoice_type.title()} billing for {subscription.pricing_tier.name}",
                metadata={
                    'generated_automatically': True,
                    'invoice_type': invoice_type,
                    'subscription_period_start': subscription.current_period_start.isoformat(),
                    'subscription_period_end': subscription.current_period_end.isoformat()
                }
            )
            
            self.db.add(invoice)
            self.db.commit()
            
            # Generate PDF invoice
            pdf_path = self._generate_invoice_pdf(invoice)
            
            # Send invoice email
            email_result = self.send_invoice_email(invoice.id, pdf_path)
            
            self._log_audit_event(
                event_type=AuditEventType.INVOICE_CREATED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                invoice_id=invoice.id,
                event_description=f"Automatic invoice generated: {invoice_number}"
            )
            
            return {
                'success': True,
                'invoice_id': invoice.id,
                'invoice_number': invoice_number,
                'amount': amount,
                'pdf_path': pdf_path,
                'email_sent': email_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error generating automatic invoice: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_invoice_amount(self, subscription: Subscription) -> float:
        """Calculate invoice amount including taxes and fees"""
        try:
            base_amount = subscription.amount
            
            # Add usage-based charges
            usage_charges = self._calculate_usage_charges(subscription)
            
            # Calculate tax
            tax_amount = self._calculate_tax_amount(subscription, base_amount + usage_charges)
            
            total_amount = base_amount + usage_charges + tax_amount
            
            return round(total_amount, 2)
            
        except Exception as e:
            logger.error(f"Error calculating invoice amount: {e}")
            return subscription.amount
    
    def _calculate_usage_charges(self, subscription: Subscription) -> float:
        """Calculate usage-based charges"""
        try:
            # This would integrate with your usage tracking system
            # For now, return 0
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating usage charges: {e}")
            return 0.0
    
    def _generate_invoice_number(self, customer_id: int) -> str:
        """Generate unique invoice number"""
        try:
            # Get count of invoices for this customer
            count = self.db.query(BillingHistory).filter(
                BillingHistory.customer_id == customer_id
            ).count()
            
            # Generate invoice number: INV-{customer_id}-{count+1}-{year}
            year = datetime.utcnow().year
            invoice_number = f"INV-{customer_id:06d}-{count+1:04d}-{year}"
            
            return invoice_number
            
        except Exception as e:
            logger.error(f"Error generating invoice number: {e}")
            return f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    def _generate_invoice_pdf(self, invoice: BillingHistory) -> str:
        """Generate PDF invoice (placeholder implementation)"""
        try:
            # This would integrate with a PDF generation library like ReportLab
            # For now, return a placeholder path
            pdf_path = f"invoices/invoice_{invoice.invoice_number}.pdf"
            
            # TODO: Implement actual PDF generation
            # pdf_content = generate_invoice_pdf(invoice)
            # save_pdf(pdf_path, pdf_content)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating invoice PDF: {e}")
            return ""
    
    # ============================================================================
    # PAYMENT RECEIPT EMAIL DELIVERY
    # ============================================================================
    
    def send_invoice_email(self, invoice_id: int, pdf_path: str = None) -> Dict[str, Any]:
        """Send invoice email to customer using Resend"""
        try:
            invoice = self.db.query(BillingHistory).filter(
                BillingHistory.id == invoice_id
            ).first()
            
            if not invoice:
                raise BillingFeaturesError("Invoice not found")
            
            customer = self.db.query(Customer).filter(
                Customer.id == invoice.customer_id
            ).first()
            
            if not customer:
                raise BillingFeaturesError("Customer not found")
            
            # Prepare invoice data
            invoice_data = {
                'invoice_number': invoice.invoice_number,
                'amount': float(invoice.amount),
                'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else 'N/A',
                'status': invoice.status,
                'created_at': invoice.created_at.strftime('%Y-%m-%d') if invoice.created_at else 'N/A'
            }
            
            # Send email via Resend
            result = resend_email_service.send_billing_email(
                user_email=customer.email,
                user_name=customer.first_name or customer.email,
                invoice_data=invoice_data,
                pdf_path=pdf_path
            )
            
            if result.get('success'):
                # Update invoice with email sent timestamp
                invoice.email_sent_at = datetime.utcnow()
                self.db.commit()
                
                self._log_audit_event(
                    event_type=AuditEventType.EMAIL_SENT,
                    customer_id=customer.id,
                    invoice_id=invoice.id,
                    event_description=f"Invoice email sent: {invoice.invoice_number}"
                )
                
                return {
                    'success': True,
                    'email_sent': True,
                    'sent_at': invoice.email_sent_at.isoformat(),
                    'email_id': result.get('email_id')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to send email')
                }
            
        except Exception as e:
            logger.error(f"Error sending invoice email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_payment_receipt_email(self, invoice_id: int) -> Dict[str, Any]:
        """Send payment receipt email"""
        try:
            invoice = self.db.query(BillingHistory).filter(
                BillingHistory.id == invoice_id
            ).first()
            
            if not invoice or not invoice.paid:
                raise BillingFeaturesError("Invoice not found or not paid")
            
            customer = self.db.query(Customer).filter(
                Customer.id == invoice.customer_id
            ).first()
            
            # Prepare email content
            subject = f"Payment Receipt - Invoice #{invoice.invoice_number}"
            html_content = self._generate_receipt_email_html(invoice, customer)
            text_content = self._generate_receipt_email_text(invoice, customer)
            
            # Send email
            email_result = self._send_email(
                to_email=customer.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            self._log_audit_event(
                event_type=AuditEventType.EMAIL_SENT,
                customer_id=customer.id,
                invoice_id=invoice.id,
                event_description=f"Payment receipt email sent: {invoice.invoice_number}"
            )
            
            return {
                'success': True,
                'email_sent': True
            }
            
        except Exception as e:
            logger.error(f"Error sending payment receipt email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        pdf_path: str = None
    ) -> bool:
        """Send email with optional PDF attachment"""
        try:
            if not all([self.smtp_username, self.smtp_password]):
                logger.warning("SMTP credentials not configured, skipping email send")
                return False
            
            # Create message
            msg = MimeMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MimeText(text_content, 'plain')
            html_part = MimeText(html_content, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add PDF attachment if provided
            if pdf_path:
                try:
                    with open(pdf_path, 'rb') as f:
                        pdf_attachment = MimeApplication(f.read(), _subtype='pdf')
                        pdf_attachment.add_header(
                            'Content-Disposition', 
                            'attachment', 
                            filename=f"invoice_{pdf_path.split('/')[-1]}"
                        )
                        msg.attach(pdf_attachment)
                except FileNotFoundError:
                    logger.warning(f"PDF file not found: {pdf_path}")
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _generate_invoice_email_html(self, invoice: BillingHistory, customer: Customer) -> str:
        """Generate HTML content for invoice email"""
        return f"""
        <html>
        <body>
            <h2>Invoice #{invoice.invoice_number}</h2>
            <p>Dear {customer.name or customer.email},</p>
            <p>Your invoice for {invoice.description} is ready.</p>
            <p><strong>Amount Due:</strong> ${invoice.amount_due:.2f} {invoice.currency}</p>
            <p><strong>Due Date:</strong> {invoice.due_date.strftime('%B %d, %Y')}</p>
            <p>Please log into your MINGUS account to view and pay this invoice.</p>
            <p>Thank you for choosing MINGUS!</p>
        </body>
        </html>
        """
    
    def _generate_invoice_email_text(self, invoice: BillingHistory, customer: Customer) -> str:
        """Generate text content for invoice email"""
        return f"""
        Invoice #{invoice.invoice_number}
        
        Dear {customer.name or customer.email},
        
        Your invoice for {invoice.description} is ready.
        
        Amount Due: ${invoice.amount_due:.2f} {invoice.currency}
        Due Date: {invoice.due_date.strftime('%B %d, %Y')}
        
        Please log into your MINGUS account to view and pay this invoice.
        
        Thank you for choosing MINGUS!
        """
    
    def _generate_receipt_email_html(self, invoice: BillingHistory, customer: Customer) -> str:
        """Generate HTML content for receipt email"""
        return f"""
        <html>
        <body>
            <h2>Payment Receipt - Invoice #{invoice.invoice_number}</h2>
            <p>Dear {customer.name or customer.email},</p>
            <p>Thank you for your payment!</p>
            <p><strong>Amount Paid:</strong> ${invoice.amount_paid:.2f} {invoice.currency}</p>
            <p><strong>Payment Date:</strong> {invoice.paid_date.strftime('%B %d, %Y')}</p>
            <p>This receipt confirms your payment for {invoice.description}.</p>
            <p>Thank you for choosing MINGUS!</p>
        </body>
        </html>
        """
    
    def _generate_receipt_email_text(self, invoice: BillingHistory, customer: Customer) -> str:
        """Generate text content for receipt email"""
        return f"""
        Payment Receipt - Invoice #{invoice.invoice_number}
        
        Dear {customer.name or customer.email},
        
        Thank you for your payment!
        
        Amount Paid: ${invoice.amount_paid:.2f} {invoice.currency}
        Payment Date: {invoice.paid_date.strftime('%B %d, %Y')}
        
        This receipt confirms your payment for {invoice.description}.
        
        Thank you for choosing MINGUS!
        """
    
    # ============================================================================
    # DUNNING MANAGEMENT FOR FAILED PAYMENTS
    # ============================================================================
    
    def process_dunning_management(self) -> Dict[str, Any]:
        """Process dunning management for failed payments"""
        try:
            # Get overdue invoices
            overdue_invoices = self._get_overdue_invoices()
            
            results = {
                'processed': 0,
                'dunning_emails_sent': 0,
                'subscriptions_suspended': 0,
                'errors': []
            }
            
            for invoice in overdue_invoices:
                try:
                    result = self._process_dunning_for_invoice(invoice)
                    results['processed'] += 1
                    
                    if result['dunning_email_sent']:
                        results['dunning_emails_sent'] += 1
                    if result['subscription_suspended']:
                        results['subscriptions_suspended'] += 1
                        
                except Exception as e:
                    results['errors'].append({
                        'invoice_id': invoice.id,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in dunning management: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_overdue_invoices(self) -> List[BillingHistory]:
        """Get invoices that are overdue for payment"""
        try:
            today = datetime.utcnow().date()
            
            overdue_invoices = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.status.in_(['pending', 'past_due']),
                    BillingHistory.paid == False,
                    func.date(BillingHistory.due_date) < today
                )
            ).all()
            
            return overdue_invoices
            
        except Exception as e:
            logger.error(f"Error getting overdue invoices: {e}")
            return []
    
    def _process_dunning_for_invoice(self, invoice: BillingHistory) -> Dict[str, Any]:
        """Process dunning for a specific invoice"""
        try:
            days_overdue = (datetime.utcnow().date() - invoice.due_date.date()).days
            
            result = {
                'dunning_email_sent': False,
                'subscription_suspended': False
            }
            
            # Send dunning emails based on overdue days
            if days_overdue == 1:
                # First reminder
                self._send_dunning_email(invoice, 'first_reminder')
                result['dunning_email_sent'] = True
                
            elif days_overdue == 3:
                # Second reminder
                self._send_dunning_email(invoice, 'second_reminder')
                result['dunning_email_sent'] = True
                
            elif days_overdue == 7:
                # Final warning
                self._send_dunning_email(invoice, 'final_warning')
                result['dunning_email_sent'] = True
                
            elif days_overdue >= 14:
                # Suspend subscription
                self._suspend_subscription_for_non_payment(invoice)
                result['subscription_suspended'] = True
                
                # Send suspension notice
                self._send_dunning_email(invoice, 'suspension_notice')
                result['dunning_email_sent'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing dunning for invoice {invoice.id}: {e}")
            return {
                'dunning_email_sent': False,
                'subscription_suspended': False,
                'error': str(e)
            }
    
    def _send_dunning_email(self, invoice: BillingHistory, dunning_type: str) -> bool:
        """Send dunning email based on type"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == invoice.customer_id
            ).first()
            
            if not customer:
                return False
            
            # Get email template based on dunning type
            subject, html_content, text_content = self._get_dunning_email_template(
                invoice, customer, dunning_type
            )
            
            # Send email
            email_sent = self._send_email(
                to_email=customer.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if email_sent:
                # Log dunning email sent
                self._log_audit_event(
                    event_type=AuditEventType.DUNNING_EMAIL_SENT,
                    customer_id=customer.id,
                    invoice_id=invoice.id,
                    event_description=f"Dunning email sent: {dunning_type}"
                )
            
            return email_sent
            
        except Exception as e:
            logger.error(f"Error sending dunning email: {e}")
            return False
    
    def _get_dunning_email_template(
        self, 
        invoice: BillingHistory, 
        customer: Customer, 
        dunning_type: str
    ) -> Tuple[str, str, str]:
        """Get dunning email template based on type"""
        days_overdue = (datetime.utcnow().date() - invoice.due_date.date()).days
        
        if dunning_type == 'first_reminder':
            subject = f"Payment Reminder - Invoice #{invoice.invoice_number}"
            html_content = f"""
            <html>
            <body>
                <h2>Payment Reminder</h2>
                <p>Dear {customer.name or customer.email},</p>
                <p>This is a friendly reminder that your invoice #{invoice.invoice_number} is overdue by {days_overdue} day(s).</p>
                <p><strong>Amount Due:</strong> ${invoice.amount_due:.2f} {invoice.currency}</p>
                <p>Please log into your MINGUS account to make payment.</p>
                <p>Thank you!</p>
            </body>
            </html>
            """
        elif dunning_type == 'second_reminder':
            subject = f"Payment Overdue - Invoice #{invoice.invoice_number}"
            html_content = f"""
            <html>
            <body>
                <h2>Payment Overdue</h2>
                <p>Dear {customer.name or customer.email},</p>
                <p>Your invoice #{invoice.invoice_number} is now {days_overdue} days overdue.</p>
                <p><strong>Amount Due:</strong> ${invoice.amount_due:.2f} {invoice.currency}</p>
                <p>Please make payment immediately to avoid service interruption.</p>
                <p>Thank you!</p>
            </body>
            </html>
            """
        elif dunning_type == 'final_warning':
            subject = f"Final Payment Warning - Invoice #{invoice.invoice_number}"
            html_content = f"""
            <html>
            <body>
                <h2>Final Payment Warning</h2>
                <p>Dear {customer.name or customer.email},</p>
                <p>Your invoice #{invoice.invoice_number} is {days_overdue} days overdue.</p>
                <p><strong>Amount Due:</strong> ${invoice.amount_due:.2f} {invoice.currency}</p>
                <p>This is your final warning. Your service will be suspended if payment is not received within 7 days.</p>
                <p>Please make payment immediately.</p>
            </body>
            </html>
            """
        else:  # suspension_notice
            subject = f"Service Suspended - Invoice #{invoice.invoice_number}"
            html_content = f"""
            <html>
            <body>
                <h2>Service Suspended</h2>
                <p>Dear {customer.name or customer.email},</p>
                <p>Your MINGUS service has been suspended due to non-payment.</p>
                <p>Invoice #{invoice.invoice_number} is {days_overdue} days overdue.</p>
                <p><strong>Amount Due:</strong> ${invoice.amount_due:.2f} {invoice.currency}</p>
                <p>Please make payment to restore your service.</p>
            </body>
            </html>
            """
        
        # Generate text version
        text_content = html_content.replace('<html>', '').replace('</html>', '').replace('<body>', '').replace('</body>', '').replace('<h2>', '').replace('</h2>', '').replace('<p>', '').replace('</p>', '\n').replace('<strong>', '').replace('</strong>', '')
        
        return subject, html_content, text_content
    
    def _suspend_subscription_for_non_payment(self, invoice: BillingHistory) -> bool:
        """Suspend subscription due to non-payment"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == invoice.subscription_id
            ).first()
            
            if subscription:
                subscription.status = 'unpaid'
                self.db.commit()
                
                self._log_audit_event(
                    event_type=AuditEventType.SUBSCRIPTION_SUSPENDED,
                    customer_id=invoice.customer_id,
                    subscription_id=subscription.id,
                    event_description=f"Subscription suspended for non-payment: Invoice #{invoice.invoice_number}"
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error suspending subscription: {e}")
            return False
    
    # ============================================================================
    # TAX CALCULATION AND COMPLIANCE
    # ============================================================================
    
    def calculate_tax(
        self,
        customer_id: int,
        amount: float,
        currency: str = 'USD',
        tax_exempt: str = None
    ) -> Dict[str, Any]:
        """Calculate tax for a transaction"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                raise BillingFeaturesError("Customer not found")
            
            # Check if customer is tax exempt
            if tax_exempt == 'exempt' or customer.tax_exempt == 'exempt':
                return {
                    'tax_amount': 0.0,
                    'tax_rate': 0.0,
                    'tax_exempt': True,
                    'tax_details': {}
                }
            
            # Get customer location for tax calculation
            customer_location = self._get_customer_location(customer)
            
            # Calculate tax using tax service
            tax_result = self._call_tax_service(
                amount=amount,
                currency=currency,
                customer_location=customer_location,
                tax_exempt=tax_exempt or customer.tax_exempt
            )
            
            return tax_result
            
        except Exception as e:
            logger.error(f"Error calculating tax: {e}")
            return {
                'tax_amount': 0.0,
                'tax_rate': 0.0,
                'error': str(e)
            }
    
    def _get_customer_location(self, customer: Customer) -> Dict[str, str]:
        """Get customer location for tax calculation"""
        try:
            # Parse customer address
            address = customer.address
            if isinstance(address, str):
                address = json.loads(address)
            
            return {
                'country': address.get('country', 'US'),
                'state': address.get('state', ''),
                'city': address.get('city', ''),
                'postal_code': address.get('postal_code', '')
            }
            
        except Exception as e:
            logger.error(f"Error parsing customer location: {e}")
            return {
                'country': 'US',
                'state': '',
                'city': '',
                'postal_code': ''
            }
    
    def _call_tax_service(
        self,
        amount: float,
        currency: str,
        customer_location: Dict[str, str],
        tax_exempt: str
    ) -> Dict[str, Any]:
        """Call external tax service for tax calculation"""
        try:
            if not self.tax_service_url or not self.tax_service_api_key:
                # Fallback to simple tax calculation
                return self._calculate_simple_tax(amount, customer_location)
            
            # Prepare request to tax service
            tax_request = {
                'amount': amount,
                'currency': currency,
                'customer_location': customer_location,
                'tax_exempt': tax_exempt,
                'api_key': self.tax_service_api_key
            }
            
            response = requests.post(
                self.tax_service_url,
                json=tax_request,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Tax service error: {response.status_code}")
                return self._calculate_simple_tax(amount, customer_location)
                
        except Exception as e:
            logger.error(f"Error calling tax service: {e}")
            return self._calculate_simple_tax(amount, customer_location)
    
    def _calculate_simple_tax(self, amount: float, customer_location: Dict[str, str]) -> Dict[str, Any]:
        """Simple tax calculation fallback"""
        try:
            # Simple US tax calculation
            country = customer_location.get('country', 'US')
            state = customer_location.get('state', '')
            
            if country == 'US':
                # Basic state tax rates (simplified)
                state_tax_rates = {
                    'CA': 0.085, 'NY': 0.08, 'TX': 0.0625, 'FL': 0.06,
                    'WA': 0.065, 'IL': 0.0625, 'PA': 0.06, 'OH': 0.0575
                }
                
                tax_rate = state_tax_rates.get(state, 0.05)  # Default 5%
                tax_amount = amount * tax_rate
                
                return {
                    'tax_amount': round(tax_amount, 2),
                    'tax_rate': tax_rate,
                    'tax_exempt': False,
                    'tax_details': {
                        'state': state,
                        'country': country,
                        'calculation_method': 'simple'
                    }
                }
            else:
                # International - no tax for now
                return {
                    'tax_amount': 0.0,
                    'tax_rate': 0.0,
                    'tax_exempt': True,
                    'tax_details': {
                        'country': country,
                        'calculation_method': 'international'
                    }
                }
                
        except Exception as e:
            logger.error(f"Error in simple tax calculation: {e}")
            return {
                'tax_amount': 0.0,
                'tax_rate': 0.0,
                'error': str(e)
            }
    
    # ============================================================================
    # CURRENCY HANDLING
    # ============================================================================
    
    def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        date: datetime = None
    ) -> Dict[str, Any]:
        """Convert amount between currencies"""
        try:
            if from_currency == to_currency:
                return {
                    'converted_amount': amount,
                    'exchange_rate': 1.0,
                    'from_currency': from_currency,
                    'to_currency': to_currency
                }
            
            if date is None:
                date = datetime.utcnow()
            
            # Get exchange rate
            exchange_rate = self._get_exchange_rate(from_currency, to_currency, date)
            
            if exchange_rate is None:
                raise BillingFeaturesError(f"Unable to get exchange rate for {from_currency} to {to_currency}")
            
            converted_amount = amount * exchange_rate
            
            return {
                'converted_amount': round(converted_amount, 2),
                'exchange_rate': exchange_rate,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'conversion_date': date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error converting currency: {e}")
            return {
                'error': str(e)
            }
    
    def _get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: datetime
    ) -> Optional[float]:
        """Get exchange rate from external API"""
        try:
            if not self.exchange_rate_api_url:
                # Fallback to hardcoded rates (for development)
                return self._get_fallback_exchange_rate(from_currency, to_currency)
            
            # Call exchange rate API
            url = f"{self.exchange_rate_api_url}/convert"
            params = {
                'from': from_currency,
                'to': to_currency,
                'date': date.strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('rate')
            else:
                logger.warning(f"Exchange rate API error: {response.status_code}")
                return self._get_fallback_exchange_rate(from_currency, to_currency)
                
        except Exception as e:
            logger.error(f"Error getting exchange rate: {e}")
            return self._get_fallback_exchange_rate(from_currency, to_currency)
    
    def _get_fallback_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get fallback exchange rates for development"""
        # Hardcoded rates (should be updated regularly in production)
        rates = {
            'USD': {
                'EUR': 0.85,
                'GBP': 0.73,
                'CAD': 1.25,
                'AUD': 1.35
            },
            'EUR': {
                'USD': 1.18,
                'GBP': 0.86,
                'CAD': 1.47,
                'AUD': 1.59
            },
            'GBP': {
                'USD': 1.37,
                'EUR': 1.16,
                'CAD': 1.71,
                'AUD': 1.85
            }
        }
        
        return rates.get(from_currency, {}).get(to_currency)
    
    def format_currency(
        self,
        amount: float,
        currency: str,
        locale: str = 'en_US'
    ) -> str:
        """Format currency amount for display"""
        try:
            # Simple currency formatting
            currency_symbols = {
                'USD': '$',
                'EUR': '€',
                'GBP': '£',
                'CAD': 'C$',
                'AUD': 'A$'
            }
            
            symbol = currency_symbols.get(currency, currency)
            formatted_amount = f"{symbol}{amount:.2f}"
            
            return formatted_amount
            
        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return f"{amount:.2f} {currency}"
    
    def get_supported_currencies(self) -> List[Dict[str, Any]]:
        """Get list of supported currencies"""
        return [
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'default': True},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'default': False},
            {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'default': False},
            {'code': 'CAD', 'name': 'Canadian Dollar', 'symbol': 'C$', 'default': False},
            {'code': 'AUD', 'name': 'Australian Dollar', 'symbol': 'A$', 'default': False}
        ]
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _log_audit_event(
        self,
        event_type: AuditEventType,
        customer_id: int = None,
        subscription_id: int = None,
        invoice_id: int = None,
        event_description: str = None,
        metadata: Dict = None
    ):
        """Log an audit event"""
        try:
            audit_log = AuditLog(
                event_type=event_type,
                customer_id=customer_id,
                subscription_id=subscription_id,
                invoice_id=invoice_id,
                event_description=event_description,
                metadata=metadata
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log audit event: {e}")
            # Don't raise exception for audit logging failures 