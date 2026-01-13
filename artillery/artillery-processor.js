// Artillery processor functions for load testing
// Custom functions and data generation

module.exports = {
  generateTestData,
  generateAssessmentData,
  generateRandomEmail,
  logResponseTime
};

/**
 * Generate test data for requests
 */
function generateTestData(context, events, done) {
  context.vars.testId = Math.random().toString(36).substring(7);
  context.vars.timestamp = new Date().toISOString();
  return done();
}

/**
 * Generate assessment data
 */
function generateAssessmentData(context, events, done) {
  const emails = [
    'user1@example.com',
    'user2@example.com',
    'user3@example.com',
    'test@example.com'
  ];
  
  const firstNames = ['John', 'Jane', 'Bob', 'Alice', 'Charlie'];
  const assessmentTypes = ['financial_wellness', 'career', 'housing'];
  const stressLevels = ['low', 'moderate', 'high', 'very_high'];
  
  context.vars.testEmail = emails[Math.floor(Math.random() * emails.length)] + 
    '-' + Math.random().toString(36).substring(7);
  context.vars.testFirstName = firstNames[Math.floor(Math.random() * firstNames.length)];
  context.vars.testAssessmentType = assessmentTypes[Math.floor(Math.random() * assessmentTypes.length)];
  context.vars.testStressLevel = stressLevels[Math.floor(Math.random() * stressLevels.length)];
  
  return done();
}

/**
 * Generate random email
 */
function generateRandomEmail(context, events, done) {
  const random = Math.random().toString(36).substring(7);
  context.vars.randomEmail = `test-${random}@example.com`;
  return done();
}

/**
 * Log response time for monitoring
 */
function logResponseTime(requestParams, response, context, events, done) {
  if (response.timings) {
    const responseTime = response.timings.response;
    events.emit('counter', 'response_time', responseTime);
    
    // Log slow requests
    if (responseTime > 1000) {
      events.emit('histogram', 'slow_requests', responseTime);
    }
  }
  return done();
}

/**
 * Check error rate
 */
function checkErrorRate(requestParams, response, context, events, done) {
  if (response.statusCode >= 400) {
    events.emit('counter', 'errors', 1);
    events.emit('counter', `errors.${response.statusCode}`, 1);
  }
  return done();
}
