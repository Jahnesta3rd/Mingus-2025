import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';
import CartHeader from './CartHeader';
import RetailerSection from './RetailerSection';
import SwapModal from './SwapModal';
import {
  normalizeTierKey,
  resolveToken,
  tierNumberFromKey,
  useProductRecommendations,
} from './hooks/useProductRecommendations';
import styles from './ProductPickerUI.module.css';

const RETAILERS = ['h&m', 'nordstrom', 'amazon'];

function emptyCart() {
  return { 'h&m': [], nordstrom: [], amazon: [] };
}

function cloneCart(source) {
  const next = emptyCart();
  for (const retailer of RETAILERS) {
    next[retailer] = Array.isArray(source?.[retailer])
      ? source[retailer].map((item) => ({ ...item }))
      : [];
  }
  return next;
}

function cartTotals(cart) {
  const byRetailer = {};
  let grandTotal = 0;
  for (const retailer of RETAILERS) {
    const items = cart?.[retailer] || [];
    const total = items.reduce(
      (sum, item) => sum + Number(item.price || 0) * (Number(item.quantity) || 1),
      0,
    );
    byRetailer[retailer] = total;
    grandTotal += total;
  }
  return { byRetailer, grandTotal };
}

function mapProductToCartItem(product, currentItem) {
  const qty = Number(currentItem?.quantity) || 1;
  return {
    category: currentItem?.category || product.category,
    productId: product.sku || product.id,
    sku: product.sku || product.id,
    name: product.name,
    quantity: qty,
    price: Number(product.price) || 0,
    imageUrl: product.image_url || product.imageUrl,
    rating: product.rating,
    reviewCount: product.review_count ?? product.reviewCount,
    color: product.color,
    reason: currentItem?.reason
      ? `Swapped: ${currentItem.reason}`
      : 'Selected alternative',
    url: product.url,
    retailer: product.retailer || currentItem?.retailer,
  };
}

/**
 * BTS6 — product picker for a purchase-plan tier.
 */
export default function ProductPickerUI() {
  const { sessionId, tier: tierParam } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { getAccessToken } = useAuth();

  const tierFromState = location.state?.tierKey || location.state?.tier || tierParam;
  const tierKey = normalizeTierKey(tierFromState) || normalizeTierKey(tierParam);
  const tierNum = tierNumberFromKey(tierKey);

  const { recommendations, loading, error } = useProductRecommendations(
    sessionId,
    tierKey,
    { getAccessToken },
  );

  const [cart, setCart] = useState(null);
  const [swapModal, setSwapModal] = useState(null);
  const [swapLoadingCategory, setSwapLoadingCategory] = useState(null);
  const [swapError, setSwapError] = useState(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    if (recommendations?.recommendations) {
      setCart(cloneCart(recommendations.recommendations));
    }
  }, [recommendations]);

  const { byRetailer, grandTotal } = useMemo(
    () => cartTotals(cart || emptyCart()),
    [cart],
  );

  const tierBudget = Number(recommendations?.summary?.tierBudget) || 0;
  const remaining = tierBudget - grandTotal;

  const handleSwapClick = async (retailer, category) => {
    setSwapError(null);
    setSwapLoadingCategory(category);
    try {
      const token = resolveToken(getAccessToken);
      if (!token) {
        throw new Error('Not logged in. Please log in and try again.');
      }

      const params = new URLSearchParams({
        category,
        retailer,
      });
      const response = await fetch(`/api/bts/products/search?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...csrfHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load alternative products');
      }

      const payload = await response.json();
      const products = Array.isArray(payload)
        ? payload
        : Array.isArray(payload?.products)
          ? payload.products
          : [];

      const currentItem = (cart?.[retailer] || []).find(
        (item) => item.category === category,
      );
      const filtered = products
        .filter((p) => p.sku !== currentItem?.sku)
        .slice(0, 5);

      setSwapModal({
        retailer,
        category,
        currentItem,
        alternatives: filtered,
      });
    } catch (err) {
      setSwapError(err instanceof Error ? err.message : 'Swap failed');
    } finally {
      setSwapLoadingCategory(null);
    }
  };

  const handleSwapItem = (newProduct) => {
    if (!swapModal?.currentItem || !cart) return;

    const mapped = mapProductToCartItem(newProduct, swapModal.currentItem);
    const currentLine =
      Number(swapModal.currentItem.price) *
      (Number(swapModal.currentItem.quantity) || 1);
    const newLine = Number(mapped.price) * (Number(mapped.quantity) || 1);
    const newTotal = grandTotal - currentLine + newLine;

    if (newTotal > tierBudget) {
      setSwapError(
        `That swap would exceed your budget by $${(newTotal - tierBudget).toFixed(2)}`,
      );
      return;
    }

    const next = cloneCart(cart);
    const list = next[swapModal.retailer] || [];
    const idx = list.findIndex((item) => item.category === swapModal.category);
    if (idx >= 0) {
      list[idx] = mapped;
    } else {
      list.push(mapped);
    }
    next[swapModal.retailer] = list;
    setCart(next);
    setSwapModal(null);
    setSwapError(null);
  };

  const handleCheckout = () => {
    setCheckoutLoading(true);
    navigate(`/bts/${sessionId}/checkout`, {
      state: {
        tier: tierNum,
        tierKey,
        tierData: location.state,
        cart,
        recommendations,
        total: grandTotal,
        budget: tierBudget,
        remaining,
      },
    });
    setCheckoutLoading(false);
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingSpinner} aria-busy="true">
          <div className={styles.spinner} />
          <p>Loading Tier {tierNum} recommendations…</p>
        </div>
      </div>
    );
  }

  if (error || !recommendations) {
    return (
      <div className={styles.container}>
        <div className={styles.errorBox} role="alert">
          <p>{error || 'Failed to load recommendations'}</p>
          <div className={styles.errorActions}>
            <button type="button" onClick={() => navigate(`/bts/${sessionId}/plan`)}>
              Back to plan
            </button>
            <button type="button" onClick={() => window.location.reload()}>
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!cart) return null;

  return (
    <div className={styles.container}>
      <CartHeader
        tier={tierNum}
        total={grandTotal}
        budget={tierBudget}
        remaining={remaining}
        byRetailer={byRetailer}
      />

      {swapError ? (
        <p className={styles.inlineError} role="alert">
          {swapError}
        </p>
      ) : null}

      {RETAILERS.map((retailer) => (
        <RetailerSection
          key={retailer}
          retailer={retailer}
          items={cart[retailer] || []}
          total={byRetailer[retailer] || 0}
          onSwap={handleSwapClick}
          swapLoadingCategory={swapLoadingCategory}
        />
      ))}

      {swapModal ? (
        <SwapModal
          modal={swapModal}
          onSwap={handleSwapItem}
          onClose={() => setSwapModal(null)}
          tierBudget={tierBudget}
          currentTotal={grandTotal}
        />
      ) : null}

      <div className={styles.footer}>
        <button
          type="button"
          className={styles.checkoutButton}
          onClick={handleCheckout}
          disabled={checkoutLoading || grandTotal <= 0}
        >
          {checkoutLoading
            ? 'Processing…'
            : `Approve & checkout ($${grandTotal.toFixed(2)})`}
        </button>
        <p className={styles.footerNote}>
          {remaining >= 0
            ? `Budget remaining: $${remaining.toFixed(2)}`
            : `Over budget by: $${Math.abs(remaining).toFixed(2)}`}
        </p>
      </div>
    </div>
  );
}
