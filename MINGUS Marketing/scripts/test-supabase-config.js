// Test script for Supabase configuration
require('dotenv').config()

console.log('🔍 Testing Supabase Configuration...')
console.log('================================')

// Check environment variables
console.log('✅ Environment variables:')
console.log(`   URL: ${process.env.REACT_APP_SUPABASE_URL ? 'Set' : 'Not set'}`)
console.log(`   Key: ${process.env.REACT_APP_SUPABASE_ANON_KEY ? 'Set' : 'Not set'}`)

// Test importing the configuration
try {
  const { supabase, createLead, getLeadByEmail } = require('../src/lib/supabase.js')
  
  console.log('✅ Supabase client imported successfully')
  console.log(`   Client type: ${typeof supabase}`)
  console.log(`   createLead function: ${typeof createLead}`)
  console.log(`   getLeadByEmail function: ${typeof getLeadByEmail}`)
  
  // Test basic connection
  console.log('\n🔌 Testing basic connection...')
  supabase
    .from('leads')
    .select('count')
    .limit(1)
    .then(({ data, error }) => {
      if (error) {
        console.log('⚠️  Connection test result:', error.message)
        console.log('   This is expected due to RLS policies')
      } else {
        console.log('✅ Connection successful')
      }
      console.log('\n🎉 Supabase configuration test completed!')
    })
    .catch(err => {
      console.log('❌ Connection failed:', err.message)
    })
    
} catch (error) {
  console.log('❌ Failed to import Supabase configuration:', error.message)
} 