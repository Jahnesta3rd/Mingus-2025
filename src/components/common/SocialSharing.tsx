import React, { useState } from 'react';
import { usePWA } from '../../hooks/usePWA';

interface SocialSharingProps {
  title: string;
  text: string;
  url?: string;
  hashtags?: string[];
  className?: string;
  variant?: 'button' | 'modal' | 'floating';
}

const SocialSharing: React.FC<SocialSharingProps> = ({
  title,
  text,
  url = window.location.href,
  hashtags = ['MingusIncome', 'CareerGrowth', 'SalaryComparison'],
  className = '',
  variant = 'button'
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(false);
  const { shareData, isOnline } = usePWA();

  const handleShare = async (platform?: string) => {
    try {
      let shareUrl = url;
      let shareText = text;

      // Platform-specific sharing
      if (platform === 'twitter') {
        shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}&hashtags=${hashtags.join(',')}`;
        window.open(shareUrl, '_blank');
      } else if (platform === 'linkedin') {
        shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
        window.open(shareUrl, '_blank');
      } else if (platform === 'facebook') {
        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
        window.open(shareUrl, '_blank');
      } else if (platform === 'whatsapp') {
        shareUrl = `https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`;
        window.open(shareUrl, '_blank');
      } else {
        // Native sharing
        const success = await shareData({ title, text, url });
        if (success) {
          setShareSuccess(true);
          setTimeout(() => setShareSuccess(false), 3000);
        }
      }
    } catch (error) {
      console.error('Share failed:', error);
    }
  };

  const ShareButton = () => (
    <button
      onClick={() => variant === 'modal' ? setIsModalOpen(true) : handleShare()}
      className={`
        inline-flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all duration-200
        bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg hover:shadow-xl
        active:scale-95 transform touch-manipulation
        ${className}
        ${!isOnline ? 'opacity-50 cursor-not-allowed' : 'hover:from-blue-700 hover:to-purple-700'}
      `}
      disabled={!isOnline}
    >
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
      </svg>
      <span>Share</span>
    </button>
  );

  const ShareModal = () => (
    <>
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm mx-auto shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Share This</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-3">
              {/* Native Share */}
              <button
                onClick={() => {
                  handleShare();
                  setIsModalOpen(false);
                }}
                className="w-full flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium transition-all active:scale-95"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
                </svg>
                <span>Share with Apps</span>
              </button>

              {/* Social Platforms */}
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => {
                    handleShare('twitter');
                    setIsModalOpen(false);
                  }}
                  className="flex items-center gap-2 p-3 rounded-xl bg-blue-400 text-white font-medium transition-all active:scale-95"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                  </svg>
                  <span>Twitter</span>
                </button>

                <button
                  onClick={() => {
                    handleShare('linkedin');
                    setIsModalOpen(false);
                  }}
                  className="flex items-center gap-2 p-3 rounded-xl bg-blue-600 text-white font-medium transition-all active:scale-95"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  <span>LinkedIn</span>
                </button>

                <button
                  onClick={() => {
                    handleShare('whatsapp');
                    setIsModalOpen(false);
                  }}
                  className="flex items-center gap-2 p-3 rounded-xl bg-green-500 text-white font-medium transition-all active:scale-95"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.488"/>
                  </svg>
                  <span>WhatsApp</span>
                </button>

                <button
                  onClick={() => {
                    handleShare('facebook');
                    setIsModalOpen(false);
                  }}
                  className="flex items-center gap-2 p-3 rounded-xl bg-blue-800 text-white font-medium transition-all active:scale-95"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                  </svg>
                  <span>Facebook</span>
                </button>
              </div>

              {/* Copy Link */}
              <button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(url);
                    setShareSuccess(true);
                    setTimeout(() => setShareSuccess(false), 3000);
                    setIsModalOpen(false);
                  } catch (error) {
                    console.error('Failed to copy link:', error);
                  }
                }}
                className="w-full flex items-center gap-3 p-4 rounded-xl bg-gray-100 text-gray-700 font-medium transition-all active:scale-95 hover:bg-gray-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Copy Link</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Toast */}
      {shareSuccess && (
        <div className="fixed bottom-4 left-4 right-4 z-50 bg-green-500 text-white p-4 rounded-lg shadow-lg flex items-center gap-3">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>Shared successfully!</span>
        </div>
      )}
    </>
  );

  const FloatingShare = () => (
    <div className="fixed bottom-6 right-6 z-40">
      <button
        onClick={() => setIsModalOpen(true)}
        className="w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95 flex items-center justify-center"
      >
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
          <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
        </svg>
      </button>
    </div>
  );

  return (
    <>
      {variant === 'button' && <ShareButton />}
      {variant === 'floating' && <FloatingShare />}
      <ShareModal />
    </>
  );
};

export default SocialSharing; 