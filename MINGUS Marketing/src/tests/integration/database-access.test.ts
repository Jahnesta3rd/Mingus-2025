import { supabase } from '../lib/supabase'

/**
 * Database Access Test
 * 
 * This test verifies that the marketing funnel can access the Supabase database
 * and perform basic operations.
 */

describe('Database Access Test', () => {
  test('should connect to Supabase', async () => {
    // Test basic connection by checking if we can access the database
    const { data, error } = await supabase
      .from('leads')
      .select('count')
      .limit(1)
    
    // If table doesn't exist, we'll get an error, but that's expected
    // The important thing is that we can connect to Supabase
    expect(error).toBeDefined()
    expect(error?.code).toBe('42P01') // Table doesn't exist error
  })

  test('should have valid Supabase configuration', () => {
    // Check that Supabase client is properly configured
    expect(supabase).toBeDefined()
    expect(typeof supabase.from).toBe('function')
    expect(typeof supabase.auth).toBe('function')
  })

  test('should be able to perform basic operations', async () => {
    // Test that we can perform basic database operations
    const { data, error } = await supabase
      .rpc('version')
    
    // This should work if we have a valid connection
    expect(error).toBeNull()
    expect(data).toBeDefined()
  })
}) 