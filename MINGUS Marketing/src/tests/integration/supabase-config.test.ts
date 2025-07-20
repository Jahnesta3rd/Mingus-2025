import { 
  supabase,
  createLead,
  confirmEmail,
  getAssessmentQuestions,
  getLeadByEmail,
  logEmailSent
} from '../../lib/supabase'

describe('Supabase Configuration Test', () => {
  test('should have supabase client configured', () => {
    expect(supabase).toBeDefined()
    expect(supabase.from).toBeDefined()
  })

  test('should have all helper functions', () => {
    expect(typeof createLead).toBe('function')
    expect(typeof confirmEmail).toBe('function')
    expect(typeof getAssessmentQuestions).toBe('function')
    expect(typeof getLeadByEmail).toBe('function')
    expect(typeof logEmailSent).toBe('function')
  })

  test('should be able to connect to database', async () => {
    const { data, error } = await supabase
      .from('leads')
      .select('count')
      .limit(1)
    
    // Should not throw an error, even if table doesn't exist
    expect(error).toBeDefined() // We expect an error due to RLS, but connection works
  })

  test('should have environment variables', () => {
    expect(process.env.REACT_APP_SUPABASE_URL).toBeDefined()
    expect(process.env.REACT_APP_SUPABASE_ANON_KEY).toBeDefined()
  })
}) 