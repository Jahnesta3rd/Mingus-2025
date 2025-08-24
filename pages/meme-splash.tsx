import React from 'react';
import { GetServerSideProps } from 'next';
import Head from 'next/head';
import MemeSplashPage from '../components/MemeSplashPage';

interface MemeSplashProps {
  user?: {
    id: number;
    email: string;
  };
}

const MemeSplash: React.FC<MemeSplashProps> = ({ user }) => {
  const handleOptOut = () => {
    // Track opt-out in analytics
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'meme_opt_out_completed', {
        event_category: 'engagement',
        event_label: 'splash_page'
      });
    }
  };

  const handleContinue = () => {
    // Track continue to dashboard
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'meme_continue_to_dashboard', {
        event_category: 'engagement',
        event_label: 'splash_page'
      });
    }
  };

  return (
    <>
      <Head>
        <title>Daily Inspiration - MINGUS</title>
        <meta name="description" content="Get your daily dose of financial motivation and inspiration with MINGUS" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      
      <MemeSplashPage 
        onOptOut={handleOptOut}
        onContinue={handleContinue}
      />
    </>
  );
};

export const getServerSideProps: GetServerSideProps = async (context) => {
  // Check if user is authenticated
  const { req, res } = context;
  
  // This would typically check for a session token or JWT
  // For now, we'll assume the user is authenticated if they reach this page
  // In a real implementation, you'd verify the session here
  
  try {
    // You could make an API call to verify the session
    // const response = await fetch(`${process.env.API_URL}/api/auth/check-auth`, {
    //   headers: {
    //     Cookie: req.headers.cookie || ''
    //   }
    // });
    
    // if (!response.ok) {
    //   return {
    //     redirect: {
    //       destination: '/login',
    //       permanent: false,
    //     },
    //   };
    // }
    
    return {
      props: {
        user: {
          id: 1, // This would come from the session
          email: 'user@example.com'
        }
      }
    };
  } catch (error) {
    console.error('Error checking authentication:', error);
    return {
      redirect: {
        destination: '/login',
        permanent: false,
      },
    };
  }
};

export default MemeSplash;
