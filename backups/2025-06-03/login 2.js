// --- Supabase setup ---
const SUPABASE_URL = 'https://qjvhwqjvhwqjvhwqjvhw.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTAxOTcsImV4cCI6MjA2MjMyNjE5N30.9AsxxhX4Nt4Qr3EZerYfpvo4doVPbxuZRMgNSgnapM8';

console.log('Initializing Supabase with URL:', SUPABASE_URL);
console.log('Supabase object available:', typeof window.supabase);

// Initialize Supabase client
let supabase;
try {
  if (typeof window.supabase === 'undefined') {
    throw new Error('Supabase library not loaded');
  }
  console.log('Creating Supabase client...');
  supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  console.log('Supabase client initialized successfully');
  
  // Test the connection
  supabase.auth.getSession().then(({ data, error }) => {
    if (error) {
      console.error('Error testing Supabase connection:', error);
    } else {
      console.log('Supabase connection test successful');
    }
  });
} catch (error) {
  console.error('Failed to initialize Supabase client:', error);
  showError('Failed to initialize authentication service. Please try again later.');
}

// --- Social logins ---
async function socialLogin(provider) {
  if (!supabase) {
    showError('Authentication service is not available. Please try again later.');
    return;
  }

  try {
    console.log(`Starting ${provider} login process...`);
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: provider,
      options: {
        redirectTo: 'http://localhost:3000/dashboard.html',
        queryParams: {
          access_type: 'offline',
          prompt: 'consent'
        }
      }
    });

    if (error) {
      console.error(`${provider} login error:`, error);
      showError(error.message || `Login with ${provider} failed. Please try again.`);
    } else {
      console.log(`${provider} login successful:`, data);
    }
  } catch (err) {
    console.error(`${provider} login error:`, err);
    showError(`An error occurred during ${provider} login. Please try again.`);
  }
}

// Add event listeners for social login buttons
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, setting up event listeners');
  const googleBtn = document.getElementById('google-login');
  const linkedinBtn = document.getElementById('linkedin-login');

  if (googleBtn) {
    console.log('Google button found, adding click listener');
    googleBtn.addEventListener('click', () => {
      console.log('Google button clicked');
      socialLogin('google');
    });
  } else {
    console.error('Google button not found');
  }

  if (linkedinBtn) {
    console.log('LinkedIn button found, adding click listener');
    linkedinBtn.addEventListener('click', () => {
      console.log('LinkedIn button clicked');
      socialLogin('linkedin');
    });
  } else {
    console.error('LinkedIn button not found');
  }
});

// --- DOM elements ---
const form = document.getElementById('login-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const termsCheckbox = document.getElementById('terms');
const errorDiv = document.getElementById('login-error');
const showTerms = document.getElementById('show-terms');
const termsModal = document.getElementById('terms-modal');
const closeTerms = document.getElementById('close-terms');

// --- Modal logic ---
showTerms.onclick = (e) => {
  e.preventDefault();
  termsModal.style.display = 'flex';
};
closeTerms.onclick = () => { termsModal.style.display = 'none'; };
window.onclick = (e) => { if (e.target === termsModal) termsModal.style.display = 'none'; };

// --- Error display ---
function showError(msg) {
  const errorDiv = document.getElementById('login-error');
  if (errorDiv) {
    errorDiv.textContent = msg;
    errorDiv.style.display = 'block';
    setTimeout(() => { errorDiv.style.display = 'none'; }, 4000);
  } else {
    console.error('Error message:', msg);
  }
}

// --- Email/password login/signup ---
form.onsubmit = async (e) => {
  e.preventDefault();
  if (!termsCheckbox.checked) {
    showError('You must agree to the Terms & Conditions.');
    return;
  }
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  if (!email || !password) {
    showError('Please enter your email and password.');
    return;
  }
  // Try sign in, if fails, try sign up
  let { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) {
    // If user not found, try sign up
    if (error.message && error.message.toLowerCase().includes('invalid login credentials')) {
      let { error: signUpError } = await supabase.auth.signUp({ email, password });
      if (signUpError) {
        showError(signUpError.message || 'Sign up failed.');
        return;
      }
      showError('Check your email to confirm your account!');
      return;
    } else {
      showError(error.message || 'Login failed.');
      return;
    }
  }
  // Success: redirect
  window.location.href = '/dashboard.html';
};

// Function to check authentication status
async function checkAuth() {
  try {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) throw error;
    return session;
  } catch (error) {
    console.error('Auth check error:', error);
    return null;
  }
}

// Function to handle redirects with message
function redirectToLogin(message) {
  const url = new URL('/login.html', window.location.origin);
  if (message) {
    url.searchParams.set('message', encodeURIComponent(message));
  }
  window.location.href = url.toString();
}

// Check for message in URL parameters on page load
document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const message = urlParams.get('message');
  if (message) {
    showError(decodeURIComponent(message));
  }
});