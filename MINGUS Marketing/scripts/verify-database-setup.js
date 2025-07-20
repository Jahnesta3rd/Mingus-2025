#!/usr/bin/env node

/**
 * Database Setup Verification Script
 * 
 * This script checks the current database configuration and provides
 * guidance on what needs to be set up for the marketing funnel.
 */

const fs = require('fs')
const path = require('path')

console.log('🔍 Database Setup Verification')
console.log('==============================')

// Check for environment files
const envFiles = [
  '.env',
  '.env.local',
  '.env.development',
  'env.production'
]

console.log('\n📁 Checking environment configuration...')

let hasEnvFile = false
let hasValidCredentials = false

for (const envFile of envFiles) {
  if (fs.existsSync(envFile)) {
    console.log(`✅ Found: ${envFile}`)
    hasEnvFile = true
    
    const content = fs.readFileSync(envFile, 'utf8')
    const hasSupabaseUrl = content.includes('REACT_APP_SUPABASE_URL=')
    const hasSupabaseKey = content.includes('REACT_APP_SUPABASE_ANON_KEY=')
    
    if (hasSupabaseUrl && hasSupabaseKey) {
      console.log(`   📋 Contains Supabase configuration`)
      
      // Check if it has placeholder values
      const hasPlaceholders = content.includes('your-project.supabase.co') || 
                             content.includes('your-anon-key') ||
                             content.includes('your_supabase_project_url')
      
      if (!hasPlaceholders) {
        console.log(`   ✅ Has actual credentials (not placeholders)`)
        hasValidCredentials = true
      } else {
        console.log(`   ⚠️  Contains placeholder values`)
      }
    } else {
      console.log(`   ❌ Missing Supabase configuration`)
    }
  }
}

if (!hasEnvFile) {
  console.log('❌ No environment files found')
}

// Check for config files
console.log('\n⚙️  Checking config files...')

const configFiles = [
  'src/config.js',
  'src/config.ts',
  'config.js',
  'config.ts',
  'src/config/index.js',
  'src/config/index.ts'
]

let hasConfigFile = false

for (const configFile of configFiles) {
  if (fs.existsSync(configFile)) {
    console.log(`✅ Found: ${configFile}`)
    hasConfigFile = true
    
    const content = fs.readFileSync(configFile, 'utf8')
    if (content.includes('supabase') || content.includes('SUPABASE')) {
      console.log(`   📋 Contains Supabase configuration`)
    } else {
      console.log(`   ❌ No Supabase configuration found`)
    }
  }
}

if (!hasConfigFile) {
  console.log('❌ No config files found')
}

// Check for Supabase client files
console.log('\n🔌 Checking Supabase client setup...')

const supabaseFiles = [
  'src/lib/supabase.ts',
  'src/lib/supabase-config.ts',
  'src/lib/supabase.js'
]

let hasSupabaseClient = false

for (const supabaseFile of supabaseFiles) {
  if (fs.existsSync(supabaseFile)) {
    console.log(`✅ Found: ${supabaseFile}`)
    hasSupabaseClient = true
  }
}

if (!hasSupabaseClient) {
  console.log('❌ No Supabase client files found')
}

// Check for database schema files
console.log('\n🗄️  Checking database schema...')

const schemaFiles = [
  'supabase-schema.sql',
  'supabase-schema-clean.sql',
  'supabase-email-automation-schema.sql',
  'database/schema.sql'
]

let hasSchemaFile = false

for (const schemaFile of schemaFiles) {
  if (fs.existsSync(schemaFile)) {
    console.log(`✅ Found: ${schemaFile}`)
    hasSchemaFile = true
  }
}

if (!hasSchemaFile) {
  console.log('❌ No database schema files found')
}

// Summary and recommendations
console.log('\n📊 Setup Summary')
console.log('================')

console.log(`Environment Files: ${hasEnvFile ? '✅' : '❌'}`)
console.log(`Valid Credentials: ${hasValidCredentials ? '✅' : '❌'}`)
console.log(`Config Files: ${hasConfigFile ? '✅' : '❌'}`)
console.log(`Supabase Client: ${hasSupabaseClient ? '✅' : '❌'}`)
console.log(`Database Schema: ${hasSchemaFile ? '✅' : '❌'}`)

console.log('\n🎯 Next Steps')
console.log('=============')

if (!hasValidCredentials) {
  console.log('1️⃣  Set up Supabase credentials:')
  console.log('   - Create a .env file with your Supabase URL and keys')
  console.log('   - Or add marketing funnel config to your existing config file')
  console.log('   - See examples/config-examples.js for config patterns')
}

if (!hasSupabaseClient) {
  console.log('2️⃣  Set up Supabase client:')
  console.log('   - Copy src/lib/supabase-config.ts to your main app')
  console.log('   - Update imports in API services')
}

if (!hasSchemaFile) {
  console.log('3️⃣  Set up database schema:')
  console.log('   - Run the SQL schema from INTEGRATION_GUIDE.md')
  console.log('   - Or use supabase-schema-clean.sql')
}

if (hasValidCredentials && hasSupabaseClient && hasSchemaFile) {
  console.log('✅ All components are ready!')
  console.log('   Run: node scripts/test-database-access.js')
} else {
  console.log('⚠️  Some components need to be set up first')
}

console.log('\n📖 For detailed instructions, see:')
console.log('   - INTEGRATION_GUIDE.md')
console.log('   - CONFIG_INTEGRATION_SUMMARY.md')
console.log('   - examples/config-examples.js') 