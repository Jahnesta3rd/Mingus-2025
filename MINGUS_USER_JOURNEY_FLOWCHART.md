# 🎯 MINGUS Personal Finance Assistant - Complete User Journey Flowchart

## **Visual Flowchart: New User Onboarding Process**

```mermaid
flowchart TD
    %% Entry Points
    A[🚀 User Arrives] --> B{Entry Point?}
    B -->|Direct URL| C[📱 Splash Screen<br/>/]
    B -->|Marketing Link| D[🎯 Welcome Page<br/>/welcome]
    B -->|External Campaign| E[📊 Marketing Funnel<br/>/marketing-funnel]
    
    %% Splash Screen Flow
    C --> F[🏠 MINGUS Branding<br/>"Be. Do. Have."<br/>Logo + Tagline]
    F --> G[🔘 "Get Started" Button]
    G --> D
    
    %% Welcome Page Flow
    D --> H[💫 Animated Sequence<br/>"BE. DO. HAVE."]
    H --> I[📋 Value Propositions<br/>• Financial Future<br/>• Health & Wealth<br/>• Plan for What Matters]
    I --> J[🔒 Trust Indicators<br/>Privacy & Security]
    J --> K[🎯 Primary CTA<br/>"Start My Forecast"]
    
    %% Registration Decision
    K --> L{User Action?}
    L -->|Register| M[📝 Registration Form<br/>/api/auth/register]
    L -->|Learn More| N[📚 Information Pages]
    N --> L
    
    %% Registration Process
    M --> O[✅ Form Validation<br/>• Email format<br/>• Password strength<br/>• Required fields]
    O --> P{Validation Pass?}
    P -->|No| Q[❌ Error Message<br/>Return to form]
    Q --> M
    P -->|Yes| R[🔍 Duplicate Check<br/>Email exists?]
    R -->|Yes| S[❌ "Email already exists"]
    S --> M
    R -->|No| T[👤 Create User Account<br/>Database entry]
    
    %% User Creation & Session
    T --> U[🔐 Session Setup<br/>user_id, email, name]
    U --> V[📊 Analytics Tracking<br/>Registration event]
    V --> W[🎯 Onboarding Check<br/>Complete?]
    
    %% Onboarding Decision
    W -->|No| X[🔄 Redirect to Onboarding<br/>/api/onboarding/choice]
    W -->|Yes| Y[🏠 Redirect to Dashboard<br/>/dashboard]
    
    %% Health Onboarding Flow
    X --> Z[💚 Health Onboarding<br/>/api/health/onboarding]
    Z --> AA[📊 Step 1: Introduction<br/>"Discover How Your Wellness<br/>Affects Your Wealth"]
    AA --> BB[🔘 "Start My Wellness Journey"]
    
    %% Step 2: Health Check-in
    BB --> CC[📝 Step 2: Health Check-in<br/>"Your First Wellness Check-in"]
    CC --> DD[📊 Collect Data<br/>• Stress level (1-10)<br/>• Sleep hours<br/>• Exercise minutes<br/>• Energy level]
    DD --> EE[🔘 "Complete Check-in"]
    
    %% Step 3: Timeline
    EE --> FF[⏰ Step 3: Timeline<br/>"Building Your Insight Timeline"]
    FF --> GG[📅 Show Expectations<br/>• Week 1: Baseline<br/>• Week 2-3: Patterns<br/>• Week 4-6: Insights<br/>• Week 8+: Analytics]
    GG --> HH[🔘 "Set Up Reminders"]
    
    %% Step 4: Goals
    HH --> II[🎯 Step 4: Goal Setting<br/>"What's Your Wellness-Wealth Goal?"]
    II --> JJ[📋 Select Goals<br/>• Reduce stress spending<br/>• Lower health costs<br/>• Improve sleep habits<br/>• Better relationships<br/>• Mindfulness practice]
    JJ --> KK[🔘 "Start My Journey"]
    
    %% Onboarding Completion
    KK --> LL[✅ Onboarding Complete<br/>Save user preferences<br/>Create health profile]
    LL --> MM[🏠 Redirect to Dashboard<br/>/api/health/dashboard]
    
    %% Dashboard Access
    MM --> NN[📊 Health Dashboard<br/>Personalized insights<br/>Wellness metrics<br/>Financial correlations]
    Y --> OO[📈 Main Dashboard<br/>Financial overview<br/>Career insights<br/>Health impact]
    
    %% Ongoing Engagement
    NN --> PP[🔄 Ongoing Engagement<br/>• Weekly check-ins<br/>• Personalized insights<br/>• Goal tracking<br/>• Recommendations]
    OO --> PP
    
    %% Error Handling
    PP --> QQ{Session Valid?}
    QQ -->|No| RR[🔐 Re-authentication<br/>/api/auth/login]
    RR --> SS[✅ Login Success]
    SS --> QQ
    QQ -->|Yes| PP
    
    %% Styling
    classDef entryPoint fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef process fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef error fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef onboarding fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    classDef dashboard fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class A,B,C,D,E entryPoint
    class F,G,H,I,J,K,M,O,T,U,V,X,Z,AA,CC,DD,FF,GG,II,JJ,LL,MM,NN,OO,PP,RR,SS process
    class L,P,R,W,QQ decision
    class BB,EE,HH,KK success
    class Q,S error
    class BB,CC,DD,EE,FF,GG,HH,II,JJ,KK,LL onboarding
    class MM,NN,OO dashboard
```

## **Detailed Step-by-Step Flow**

### **Phase 1: Discovery & Landing**
```
User Arrives → Splash Screen → Welcome Page → Value Props → Registration Decision
```

### **Phase 2: Account Creation**
```
Registration Form → Validation → User Creation → Session Setup → Onboarding Check
```

### **Phase 3: Health Onboarding (4 Steps)**
```
Step 1: Introduction → Step 2: Health Check-in → Step 3: Timeline → Step 4: Goals
```

### **Phase 4: Dashboard Access**
```
Onboarding Complete → Dashboard Redirect → Personalized Experience → Ongoing Engagement
```

## **Key Decision Points**

1. **Entry Point Selection**: How user arrives (direct, marketing, external)
2. **Registration Decision**: Whether to create account or learn more
3. **Validation Gates**: Form validation, duplicate checks, password strength
4. **Onboarding Status**: Whether user has completed onboarding
5. **Session Management**: Authentication state and re-authentication

## **Error Handling & Recovery**

- **Form Validation Errors**: Return to form with specific error messages
- **Duplicate Email**: Clear error message with login suggestion
- **Session Expiry**: Automatic re-authentication flow
- **Onboarding Incomplete**: Redirect to appropriate onboarding step

## **Success Metrics & Analytics**

- **Registration Completion Rate**: Splash → Welcome → Registration → Success
- **Onboarding Completion Rate**: 4-step health onboarding completion
- **Dashboard Engagement**: Time spent, features used, return visits
- **Health Check-in Adherence**: Weekly check-in completion rates

---

## **Technical Implementation Notes**

### **Route Structure**
```
/ → Splash Screen
/welcome → Welcome Page
/api/auth/register → Registration API
/api/health/onboarding → Health Onboarding
/api/health/dashboard → Health Dashboard
/dashboard → Main Dashboard
```

### **Session Management**
- User session established after successful registration
- Session persists through onboarding flow
- Dashboard access requires valid session + completed onboarding

### **Data Flow**
1. **Registration**: User data → Database → Session → Onboarding
2. **Onboarding**: Health data → Profile creation → Dashboard access
3. **Dashboard**: Personalized insights based on collected data

### **Mobile Responsiveness**
- All templates are mobile-first responsive
- Touch-friendly interactions throughout
- Progressive web app capabilities

---

*This flowchart represents the complete user journey for new users joining the MINGUS personal finance assistant platform, with a focus on the health-wellness integration that differentiates the platform.* 