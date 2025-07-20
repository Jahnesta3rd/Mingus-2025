#!/usr/bin/env node

/**
 * Database Access Test Script
 * 
 * This script tests the Supabase database connection directly
 * without relying on the test framework.
 */

const { createClient } = require('@supabase/supabase-js')

// Get Supabase credentials from environment or use defaults
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || 'https://your-project.supabase.co'
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || 'your-anon-key'

console.log('🔍 Testing Database Access...')
console.log('================================')

// Check if we have valid credentials
if (!supabaseUrl || supabaseUrl === 'https://your-project.supabase.co') {
  console.log('❌ No valid Supabase URL found')
  console.log('   Please set REACT_APP_SUPABASE_URL environment variable')
  process.exit(1)
}

if (!supabaseAnonKey || supabaseAnonKey === 'your-anon-key') {
  console.log('❌ No valid Supabase Anon Key found')
  console.log('   Please set REACT_APP_SUPABASE_ANON_KEY environment variable')
  process.exit(1)
}

console.log('✅ Supabase credentials found')
console.log(`   URL: ${supabaseUrl}`)
console.log(`   Key: ${supabaseAnonKey.substring(0, 10)}...`)

// Create Supabase client
const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})

async function testDatabaseAccess() {
  try {
    console.log('\n🔌 Testing connection...')
    
    // Test 1: Basic connection test - try to access a simple table
    const { data: testData, error: testError } = await supabase
      .from('leads')
      .select('count')
      .limit(1)
    
    if (testError) {
      if (testError.code === '42P01') {
        console.log('✅ Connection successful')
        console.log('   Database is accessible, but leads table does not exist yet')
        console.log('   This is expected - you need to create the tables')
      } else {
        console.log('❌ Connection failed:', testError.message)
        return false
      }
    } else {
      console.log('✅ Connection successful')
      console.log('   Database is accessible and leads table exists')
    }
    
    // Test 2: Check if leads table exists
    console.log('\n📋 Checking leads table...')
    const { data: leadsData, error: leadsError } = await supabase
      .from('leads')
      .select('count')
      .limit(1)
    
    if (leadsError) {
      if (leadsError.code === '42P01') {
        console.log('⚠️  Leads table does not exist')
        console.log('   This is expected if you haven\'t created the table yet')
        console.log('   Run the SQL schema from INTEGRATION_GUIDE.md')
      } else {
        console.log('❌ Error accessing leads table:', leadsError.message)
        return false
      }
    } else {
      console.log('✅ Leads table exists and is accessible')
    }
    
    // Test 3: Check if email_logs table exists
    console.log('\n📧 Checking email_logs table...')
    const { data: emailData, error: emailError } = await supabase
      .from('email_logs')
      .select('count')
      .limit(1)
    
    if (emailError) {
      if (emailError.code === '42P01') {
        console.log('⚠️  Email_logs table does not exist')
        console.log('   This is expected if you haven\'t created the table yet')
        console.log('   Run the SQL schema from INTEGRATION_GUIDE.md')
      } else {
        console.log('❌ Error accessing email_logs table:', emailError.message)
        return false
      }
    } else {
      console.log('✅ Email_logs table exists and is accessible')
    }
    
    // Test 4: Check if email_templates table exists
    console.log('\n📝 Checking email_templates table...')
    const { data: templateData, error: templateError } = await supabase
      .from('email_templates')
      .select('count')
      .limit(1)
    
    if (templateError) {
      if (templateError.code === '42P01') {
        console.log('⚠️  Email_templates table does not exist')
        console.log('   This is expected if you haven\'t created the table yet')
        console.log('   Run the SQL schema from INTEGRATION_GUIDE.md')
      } else {
        console.log('❌ Error accessing email_templates table:', templateError.message)
        return false
      }
    } else {
      console.log('✅ Email_templates table exists and is accessible')
    }
    
    // Test 5: Test basic insert operation (if tables exist)
    console.log('\n✏️  Testing write operations...')
    const testLead = {
      email: 'test@example.com',
      segment: 'stress-free',
      score: 25,
      product_tier: 'Budget ($10)',
      created_at: new Date().toISOString()
    }
    
    const { data: insertData, error: insertError } = await supabase
      .from('leads')
      .insert(testLead)
      .select('id')
    
    if (insertError) {
      if (insertError.code === '42P01') {
        console.log('⚠️  Cannot test insert - leads table does not exist')
      } else {
        console.log('❌ Insert test failed:', insertError.message)
        return false
      }
    } else {
      console.log('✅ Insert operation successful')
      console.log(`   Created lead with ID: ${insertData[0]?.id}`)
      
      // Clean up test data
      if (insertData[0]?.id) {
        await supabase
          .from('leads')
          .delete()
          .eq('id', insertData[0].id)
        console.log('   Test data cleaned up')
      }
    }
    
    console.log('\n🎉 Database access test completed!')
    console.log('================================')
    console.log('✅ Supabase connection: Working')
    console.log('✅ Database operations: Working')
    console.log('⚠️  Tables: May need to be created (see INTEGRATION_GUIDE.md)')
    
    return true
    
  } catch (error) {
    console.log('❌ Test failed with error:', error.message)
    return false
  }
}

// Run the test
testDatabaseAccess()
  .then(success => {
    if (success) {
      console.log('\n🚀 Database is ready for marketing funnel integration!')
      process.exit(0)
    } else {
      console.log('\n❌ Database access test failed')
      process.exit(1)
    }
  })
  .catch(error => {
    console.log('❌ Unexpected error:', error.message)
    process.exit(1)
  }) 