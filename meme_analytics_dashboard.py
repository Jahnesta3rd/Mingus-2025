#!/usr/bin/env python3
"""
Meme Analytics Dashboard Application

A standalone dashboard application for viewing meme analytics with:
- Real-time metrics display
- Interactive charts and visualizations
- Alert management
- Report generation
- CSV export functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import threading
import json
from datetime import datetime, timedelta
import webbrowser
from pathlib import Path

# Import our analytics system
from meme_analytics_system import MemeAnalyticsSystem

class MemeAnalyticsDashboard:
    """Main dashboard application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Meme Analytics Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize analytics system
        self.analytics = MemeAnalyticsSystem()
        
        # Data storage
        self.current_data = {}
        self.alerts = []
        
        # Create the interface
        self.create_widgets()
        self.load_initial_data()
        
        # Auto-refresh every 30 seconds
        self.auto_refresh()
    
    def create_widgets(self):
        """Create the dashboard widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎭 Meme Analytics Dashboard", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel for controls and metrics
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Right panel for charts
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create left panel widgets
        self.create_control_panel(left_panel)
        self.create_metrics_panel(left_panel)
        self.create_alerts_panel(left_panel)
        
        # Create right panel widgets
        self.create_charts_panel(right_panel)
    
    def create_control_panel(self, parent):
        """Create the control panel"""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Time period selection
        ttk.Label(control_frame, text="Time Period:").pack(anchor=tk.W)
        self.time_period = ttk.Combobox(control_frame, values=[7, 14, 30, 60, 90], 
                                       state="readonly", width=10)
        self.time_period.set(30)
        self.time_period.pack(anchor=tk.W, pady=(0, 10))
        
        # Refresh button
        refresh_btn = ttk.Button(control_frame, text="🔄 Refresh Data", 
                                command=self.refresh_data)
        refresh_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Export buttons
        export_frame = ttk.Frame(control_frame)
        export_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(export_frame, text="📊 Export CSV", 
                  command=self.export_csv).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="📄 Generate Report", 
                  command=self.generate_report).pack(side=tk.LEFT)
        
        # Web dashboard button
        web_btn = ttk.Button(control_frame, text="🌐 Open Web Dashboard", 
                            command=self.open_web_dashboard)
        web_btn.pack(fill=tk.X, pady=(5, 0))
    
    def create_metrics_panel(self, parent):
        """Create the metrics display panel"""
        metrics_frame = ttk.LabelFrame(parent, text="Key Metrics", padding="10")
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create metrics labels
        self.metrics_labels = {}
        metrics = [
            ('total_views', 'Total Views'),
            ('unique_users', 'Unique Users'),
            ('skip_rate', 'Skip Rate (%)'),
            ('continue_rate', 'Continue Rate (%)'),
            ('avg_time_spent', 'Avg Time Spent (s)'),
            ('total_sessions', 'Total Sessions')
        ]
        
        for i, (key, label) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(metrics_frame, text=f"{label}:").grid(row=row, column=col, 
                                                           sticky=tk.W, padx=(0, 5))
            value_label = ttk.Label(metrics_frame, text="0", font=('Arial', 10, 'bold'))
            value_label.grid(row=row, column=col+1, sticky=tk.W)
            self.metrics_labels[key] = value_label
    
    def create_alerts_panel(self, parent):
        """Create the alerts panel"""
        alerts_frame = ttk.LabelFrame(parent, text="Active Alerts", padding="10")
        alerts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Alerts listbox with scrollbar
        list_frame = ttk.Frame(alerts_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.alerts_listbox = tk.Listbox(list_frame, height=6)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.alerts_listbox.yview)
        self.alerts_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.alerts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Alert count label
        self.alert_count_label = ttk.Label(alerts_frame, text="No alerts")
        self.alert_count_label.pack(pady=(5, 0))
    
    def create_charts_panel(self, parent):
        """Create the charts panel"""
        charts_frame = ttk.LabelFrame(parent, text="Analytics Charts", padding="10")
        charts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for multiple chart tabs
        self.notebook = ttk.Notebook(charts_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Daily engagement tab
        self.daily_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.daily_frame, text="Daily Engagement")
        
        # Category performance tab
        self.category_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.category_frame, text="Category Performance")
        
        # Performance summary tab
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Performance Summary")
    
    def load_initial_data(self):
        """Load initial data"""
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh all data"""
        def refresh_thread():
            try:
                days = int(self.time_period.get())
                
                # Get performance metrics
                metrics = self.analytics.get_performance_metrics(days)
                self.current_data['metrics'] = metrics
                
                # Get category performance
                category_data = self.analytics.get_category_performance(days)
                self.current_data['category_data'] = category_data
                
                # Get daily engagement
                daily_data = self.analytics.get_daily_engagement_rates(days)
                self.current_data['daily_data'] = daily_data
                
                # Get alerts
                self.alerts = self.analytics.check_alerts()
                
                # Update UI in main thread
                self.root.after(0, self.update_ui)
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to refresh data: {e}"))
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def update_ui(self):
        """Update the UI with current data"""
        # Update metrics
        metrics = self.current_data.get('metrics', {})
        for key, label in self.metrics_labels.items():
            value = metrics.get(key, 0)
            if key in ['skip_rate', 'continue_rate']:
                label.config(text=f"{value:.1f}%")
            elif key == 'avg_time_spent':
                label.config(text=f"{value:.1f}s")
            else:
                label.config(text=f"{value:,}")
        
        # Update alerts
        self.alerts_listbox.delete(0, tk.END)
        if self.alerts:
            for alert in self.alerts:
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(alert.get('severity', 'low'), "⚪")
                self.alerts_listbox.insert(tk.END, f"{severity_icon} {alert.get('title', 'Unknown Alert')}")
            self.alert_count_label.config(text=f"{len(self.alerts)} active alerts")
        else:
            self.alert_count_label.config(text="No alerts")
        
        # Update charts
        self.update_charts()
    
    def update_charts(self):
        """Update the charts"""
        try:
            # Clear existing charts
            for frame in [self.daily_frame, self.category_frame, self.summary_frame]:
                for widget in frame.winfo_children():
                    widget.destroy()
            
            # Daily engagement chart
            self.create_daily_chart()
            
            # Category performance chart
            self.create_category_chart()
            
            # Performance summary chart
            self.create_summary_chart()
            
        except Exception as e:
            print(f"Error updating charts: {e}")
    
    def create_daily_chart(self):
        """Create daily engagement chart"""
        daily_data = self.current_data.get('daily_data')
        if daily_data is None or daily_data.empty:
            ttk.Label(self.daily_frame, text="No daily data available").pack(expand=True)
            return
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        ax.plot(daily_data['date'], daily_data['skip_rate'], label='Skip Rate', marker='o')
        ax.plot(daily_data['date'], daily_data['continue_rate'], label='Continue Rate', marker='s')
        ax.plot(daily_data['date'], daily_data['engagement_rate'], label='Engagement Rate', marker='^')
        
        ax.set_title('Daily Engagement Rates')
        ax.set_ylabel('Rate (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, self.daily_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_category_chart(self):
        """Create category performance chart"""
        category_data = self.current_data.get('category_data')
        if category_data is None or category_data.empty:
            ttk.Label(self.category_frame, text="No category data available").pack(expand=True)
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Category views
        category_data_sorted = category_data.sort_values('total_views', ascending=True)
        ax1.barh(category_data_sorted['category'], category_data_sorted['total_views'])
        ax1.set_title('Total Views by Category')
        ax1.set_xlabel('Views')
        
        # Category skip rates
        ax2.bar(category_data['category'], category_data['skip_rate'])
        ax2.set_title('Skip Rate by Category')
        ax2.set_ylabel('Skip Rate (%)')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.category_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_summary_chart(self):
        """Create performance summary chart"""
        metrics = self.current_data.get('metrics', {})
        if not metrics:
            ttk.Label(self.summary_frame, text="No metrics data available").pack(expand=True)
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
        
        # Key metrics pie chart
        labels = ['Continues', 'Skips', 'Auto Advances']
        sizes = [metrics.get('total_continues', 0), metrics.get('total_skips', 0), 
                metrics.get('total_auto_advances', 0)]
        colors = ['#2ecc71', '#e74c3c', '#f39c12']
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('User Actions Distribution')
        
        # Engagement metrics
        engagement_data = [metrics.get('continue_rate', 0), metrics.get('skip_rate', 0), 
                          metrics.get('error_rate', 0)]
        engagement_labels = ['Continue Rate', 'Skip Rate', 'Error Rate']
        ax2.bar(engagement_labels, engagement_data, color=['#2ecc71', '#e74c3c', '#e67e22'])
        ax2.set_title('Engagement Metrics (%)')
        ax2.set_ylabel('Rate (%)')
        ax2.tick_params(axis='x', rotation=45)
        
        # Time spent
        ax3.bar(['Avg Time Spent'], [metrics.get('avg_time_spent', 0)], color='#3498db')
        ax3.set_title('Average Time Spent (seconds)')
        ax3.set_ylabel('Seconds')
        
        # User activity
        activity_data = [metrics.get('unique_users', 0), metrics.get('total_sessions', 0)]
        activity_labels = ['Unique Users', 'Total Sessions']
        ax4.bar(activity_labels, activity_data, color=['#9b59b6', '#1abc9c'])
        ax4.set_title('User Activity')
        ax4.set_ylabel('Count')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.summary_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def export_csv(self):
        """Export data to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save CSV Export"
            )
            
            if filename:
                days = int(self.time_period.get())
                
                # Export daily engagement data
                daily_data = self.analytics.get_daily_engagement_rates(days)
                if not daily_data.empty:
                    daily_data.to_csv(filename, index=False)
                    messagebox.showinfo("Success", f"Data exported to {filename}")
                else:
                    messagebox.showwarning("Warning", "No data available for export")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")
    
    def generate_report(self):
        """Generate and save analytics report"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Analytics Report"
            )
            
            if filename:
                days = int(self.time_period.get())
                report = self.analytics.generate_report(days)
                
                with open(filename, 'w') as f:
                    f.write(report)
                
                messagebox.showinfo("Success", f"Report saved to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")
    
    def open_web_dashboard(self):
        """Open the web dashboard in browser"""
        try:
            webbrowser.open("http://localhost:5001/api/analytics/dashboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open web dashboard: {e}")
    
    def auto_refresh(self):
        """Auto-refresh data every 30 seconds"""
        self.refresh_data()
        # Schedule next refresh
        self.root.after(30000, self.auto_refresh)
    
    def run(self):
        """Run the dashboard application"""
        self.root.mainloop()

def main():
    """Main function"""
    try:
        dashboard = MemeAnalyticsDashboard()
        dashboard.run()
    except Exception as e:
        print(f"Error starting dashboard: {e}")

if __name__ == "__main__":
    main()
