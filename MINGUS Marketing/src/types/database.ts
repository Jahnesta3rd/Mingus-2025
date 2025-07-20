export interface Database {
  public: {
    Tables: {
      leads: {
        Row: {
          id: string
          email: string
          name: string | null
          phone: string | null
          segment: string
          score: number
          product_tier: string
          created_at: string
          confirmed: boolean
          assessment_completed: boolean
          assessment_answers: Record<string, any>
          email_sequence_sent: number
          last_email_sent: string | null
          email_preferences: {
            marketing: boolean
            transactional: boolean
            frequency: 'daily' | 'weekly' | 'monthly'
          }
          engagement_metrics: {
            emails_opened: number
            emails_clicked: number
            last_engaged: string | null
          }
          ab_test_group: string | null
        }
        Insert: {
          id?: string
          email: string
          name?: string | null
          phone?: string | null
          segment?: string
          score?: number
          product_tier?: string
          created_at?: string
          confirmed?: boolean
          assessment_completed?: boolean
          assessment_answers?: Record<string, any>
          email_sequence_sent?: number
          last_email_sent?: string | null
          email_preferences?: {
            marketing: boolean
            transactional: boolean
            frequency: 'daily' | 'weekly' | 'monthly'
          }
          engagement_metrics?: {
            emails_opened: number
            emails_clicked: number
            last_engaged: string | null
          }
          ab_test_group?: string | null
        }
        Update: {
          id?: string
          email?: string
          name?: string | null
          phone?: string | null
          segment?: string
          score?: number
          product_tier?: string
          created_at?: string
          confirmed?: boolean
          assessment_completed?: boolean
          assessment_answers?: Record<string, any>
          email_sequence_sent?: number
          last_email_sent?: string | null
          email_preferences?: {
            marketing: boolean
            transactional: boolean
            frequency: 'daily' | 'weekly' | 'monthly'
          }
          engagement_metrics?: {
            emails_opened: number
            emails_clicked: number
            last_engaged: string | null
          }
          ab_test_group?: string | null
        }
      }
      email_logs: {
        Row: {
          id: string
          lead_id: string
          email_type: string
          subject: string
          body: string
          sent_at: string
          status: string
          opened_at: string | null
          clicked_at: string | null
          template_id: string | null
          campaign_id: string | null
        }
        Insert: {
          id?: string
          lead_id: string
          email_type: string
          subject: string
          body: string
          sent_at?: string
          status?: string
          opened_at?: string | null
          clicked_at?: string | null
          template_id?: string | null
          campaign_id?: string | null
        }
        Update: {
          id?: string
          lead_id?: string
          email_type?: string
          subject?: string
          body?: string
          sent_at?: string
          status?: string
          opened_at?: string | null
          clicked_at?: string | null
          template_id?: string | null
          campaign_id?: string | null
        }
      }
      assessment_questions: {
        Row: {
          id: string
          question_text: string
          question_type: string
          options: string[] | null
          category: string
          weight: number
          order_index: number
          is_active: boolean
        }
        Insert: {
          id?: string
          question_text: string
          question_type: string
          options?: string[] | null
          category: string
          weight?: number
          order_index?: number
          is_active?: boolean
        }
        Update: {
          id?: string
          question_text?: string
          question_type?: string
          options?: string[] | null
          category?: string
          weight?: number
          order_index?: number
          is_active?: boolean
        }
      }
      assessment_responses: {
        Row: {
          id: string
          lead_id: string
          question_id: string
          response: string
          created_at: string
        }
        Insert: {
          id?: string
          lead_id: string
          question_id: string
          response: string
          created_at?: string
        }
        Update: {
          id?: string
          lead_id?: string
          question_id?: string
          response?: string
          created_at?: string
        }
      }
      email_templates: {
        Row: {
          id: string
          name: string
          subject: string
          body: string
          template_type: string
          segment: string | null
          is_active: boolean
          created_at: string
          variables: string[]
        }
        Insert: {
          id?: string
          name: string
          subject: string
          body: string
          template_type: string
          segment?: string | null
          is_active?: boolean
          created_at?: string
          variables?: string[]
        }
        Update: {
          id?: string
          name?: string
          subject?: string
          body?: string
          template_type?: string
          segment?: string | null
          is_active?: boolean
          created_at?: string
          variables?: string[]
        }
      }
      email_campaigns: {
        Row: {
          id: string
          name: string
          description: string
          template_id: string
          trigger_type: string
          delay_hours: number
          is_active: boolean
          created_at: string
          sent_count: number
          open_rate: number
          click_rate: number
        }
        Insert: {
          id?: string
          name: string
          description: string
          template_id: string
          trigger_type: string
          delay_hours?: number
          is_active?: boolean
          created_at?: string
          sent_count?: number
          open_rate?: number
          click_rate?: number
        }
        Update: {
          id?: string
          name?: string
          description?: string
          template_id?: string
          trigger_type?: string
          delay_hours?: number
          is_active?: boolean
          created_at?: string
          sent_count?: number
          open_rate?: number
          click_rate?: number
        }
      }
      ab_tests: {
        Row: {
          id: string
          name: string
          description: string
          test_type: string
          variants: Record<string, any>
          traffic_split: Record<string, number>
          is_active: boolean
          start_date: string
          end_date: string | null
          created_at: string
        }
        Insert: {
          id?: string
          name: string
          description: string
          test_type: string
          variants: Record<string, any>
          traffic_split: Record<string, number>
          is_active?: boolean
          start_date: string
          end_date?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          name?: string
          description?: string
          test_type?: string
          variants?: Record<string, any>
          traffic_split?: Record<string, number>
          is_active?: boolean
          start_date?: string
          end_date?: string | null
          created_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
} 