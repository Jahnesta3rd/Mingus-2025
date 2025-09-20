import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, X, User, Briefcase, Calendar, Award, TrendingUp, MapPin, DollarSign, Star } from 'lucide-react';

interface ResumeUploadDemoProps {
  className?: string;
}

const ResumeUploadDemo: React.FC<ResumeUploadDemoProps> = ({ className = '' }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [parsedData, setParsedData] = useState<any>(null);
  const [formData, setFormData] = useState({
    jobTitle: '',
    yearsExperience: '',
    skillsSummary: '',
    location: '',
    targetSalary: ''
  });
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file: File) => {
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a PDF, DOC, or DOCX file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setUploadedFile(file);
    setError(null);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleUpload = async () => {
    if (!uploadedFile) {
      setError('Please select a file to upload');
      return;
    }

    if (!formData.jobTitle || !formData.yearsExperience) {
      setError('Please fill in all required fields');
      return;
    }

    setUploading(true);
    setError(null);
    setCurrentStep(2);

    try {
      // Simulate resume parsing
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock parsed data
      const mockParsedData = {
        personalInfo: {
          name: "Maya Johnson",
          email: "maya.johnson@example.com",
          phone: "(404) 555-0127",
          location: "Atlanta, GA"
        },
        experience: [
          {
            title: "Marketing Coordinator",
            company: "Emory Healthcare Partners",
            duration: "June 2022 - Present",
            description: "Manage social media presence across 5 platforms, increasing engagement by 45% year-over-year"
          },
          {
            title: "Marketing Assistant", 
            company: "Atlanta Medical Center",
            duration: "September 2020 - May 2022",
            description: "Assisted in developing marketing materials for 3 specialty departments"
          }
        ],
        education: {
          degree: "Bachelor of Arts in Communications",
          school: "Georgia State University",
          year: "2019"
        },
        skills: [
          "Google Analytics", "Google Ads", "Facebook Ads Manager",
          "HubSpot", "Mailchimp", "Social Media Strategy",
          "Email Marketing", "Content Creation", "Event Planning"
        ],
        certifications: [
          "Google Analytics Certified (2023)",
          "HubSpot Content Marketing Certification (2023)",
          "Facebook Blueprint Certification (2022)"
        ]
      };
      
      setParsedData(mockParsedData);
      setUploadSuccess(true);
      setUploading(false);
      setCurrentStep(3);
    } catch (err) {
      setError('Upload failed. Please try again.');
      setUploading(false);
      setCurrentStep(1);
    }
  };

  const resetForm = () => {
    setUploadedFile(null);
    setUploadSuccess(false);
    setError(null);
    setCurrentStep(1);
    setParsedData(null);
    setFormData({
      jobTitle: '',
      yearsExperience: '',
      skillsSummary: '',
      location: '',
      targetSalary: ''
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={`min-h-screen bg-gray-50 py-8 ${className}`}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Resume Upload & Job Recommendations
          </h1>
          <p className="text-gray-600 max-w-3xl mx-auto">
            Upload your resume and get personalized job recommendations with salary insights, 
            career progression paths, and application strategies tailored to your experience level.
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-8">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  currentStep >= step 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {step}
                </div>
                <span className={`ml-2 text-sm font-medium ${
                  currentStep >= step ? 'text-blue-600' : 'text-gray-500'
                }`}>
                  {step === 1 ? 'Upload Resume' : step === 2 ? 'Parse & Analyze' : 'Get Recommendations'}
                </span>
                {step < 3 && (
                  <div className={`w-16 h-0.5 ml-4 ${
                    currentStep > step ? 'bg-blue-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step 1: Upload */}
        {currentStep === 1 && (
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
              <FileText className="w-6 h-6 mr-2 text-blue-600" />
              Step 1: Upload Your Resume
            </h2>

            {/* File Upload Area */}
            <div
              className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive 
                  ? 'border-blue-400 bg-blue-50' 
                  : uploadedFile 
                    ? 'border-green-400 bg-green-50' 
                    : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileInput}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              
              {uploadedFile ? (
                <div className="space-y-4">
                  <CheckCircle className="w-12 h-12 text-green-500 mx-auto" />
                  <div>
                    <p className="text-lg font-medium text-gray-900">{uploadedFile.name}</p>
                    <p className="text-sm text-gray-500">
                      {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={() => setUploadedFile(null)}
                    className="text-red-600 hover:text-red-700 text-sm font-medium"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                  <div>
                    <p className="text-lg font-medium text-gray-900">
                      Drop your resume here, or click to browse
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      Supports PDF, DOC, and DOCX files up to 10MB
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Form Fields */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Briefcase className="w-4 h-4 inline mr-1" />
                  Current/Desired Job Title *
                </label>
                <input
                  type="text"
                  name="jobTitle"
                  value={formData.jobTitle}
                  onChange={handleInputChange}
                  placeholder="e.g., Marketing Coordinator"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Calendar className="w-4 h-4 inline mr-1" />
                  Years of Experience *
                </label>
                <input
                  type="number"
                  name="yearsExperience"
                  value={formData.yearsExperience}
                  onChange={handleInputChange}
                  placeholder="e.g., 2.5"
                  min="0"
                  max="50"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <MapPin className="w-4 h-4 inline mr-1" />
                  Preferred Location
                </label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  placeholder="e.g., Atlanta, GA"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <DollarSign className="w-4 h-4 inline mr-1" />
                  Target Salary
                </label>
                <input
                  type="text"
                  name="targetSalary"
                  value={formData.targetSalary}
                  onChange={handleInputChange}
                  placeholder="e.g., $60,000"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Award className="w-4 h-4 inline mr-1" />
                Key Skills Summary (Optional)
              </label>
              <textarea
                name="skillsSummary"
                value={formData.skillsSummary}
                onChange={handleInputChange}
                placeholder="e.g., Google Analytics, Social Media Management, Email Marketing, Content Creation..."
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <p className="text-red-700">{error}</p>
              </div>
            )}

            {/* Upload Button */}
            <div className="mt-8">
              <button
                onClick={handleUpload}
                disabled={!uploadedFile || uploading || !formData.jobTitle || !formData.yearsExperience}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Processing Resume...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5 mr-2" />
                    Upload & Analyze Resume
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Processing */}
        {currentStep === 2 && (
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
              <FileText className="w-6 h-6 mr-2 text-blue-600" />
              Step 2: Analyzing Your Resume
            </h2>

            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Processing Your Resume</h3>
              <p className="text-gray-600 mb-6">
                Our AI is extracting your skills, experience, and career objectives...
              </p>
              
              <div className="space-y-3 max-w-md mx-auto">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Extracting contact information</span>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Analyzing work experience</span>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Identifying skills and certifications</span>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Generating job recommendations</span>
                  <div className="w-4 h-4 border-2 border-gray-300 rounded"></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Results */}
        {currentStep === 3 && parsedData && (
          <div className="space-y-8">
            {/* Parsed Resume Data */}
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
                <CheckCircle className="w-6 h-6 mr-2 text-green-600" />
                Resume Analysis Complete
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Personal Info */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center">
                    <User className="w-5 h-5 mr-2 text-blue-600" />
                    Personal Information
                  </h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="font-medium">Name:</span> {parsedData.personalInfo.name}</p>
                    <p><span className="font-medium">Email:</span> {parsedData.personalInfo.email}</p>
                    <p><span className="font-medium">Phone:</span> {parsedData.personalInfo.phone}</p>
                    <p><span className="font-medium">Location:</span> {parsedData.personalInfo.location}</p>
                  </div>
                </div>

                {/* Experience */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center">
                    <Briefcase className="w-5 h-5 mr-2 text-blue-600" />
                    Work Experience
                  </h3>
                  <div className="space-y-3">
                    {parsedData.experience.map((exp: any, index: number) => (
                      <div key={index} className="border-l-2 border-blue-200 pl-3">
                        <p className="font-medium text-sm">{exp.title}</p>
                        <p className="text-xs text-gray-600">{exp.company} • {exp.duration}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Skills */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center">
                    <Award className="w-5 h-5 mr-2 text-blue-600" />
                    Skills & Certifications
                  </h3>
                  <div className="space-y-2">
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-1">Skills:</p>
                      <div className="flex flex-wrap gap-1">
                        {parsedData.skills.map((skill: string, index: number) => (
                          <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-1">Certifications:</p>
                      <div className="space-y-1">
                        {parsedData.certifications.map((cert: string, index: number) => (
                          <p key={index} className="text-xs text-gray-600">• {cert}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Education */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center">
                    <Award className="w-5 h-5 mr-2 text-blue-600" />
                    Education
                  </h3>
                  <div className="text-sm">
                    <p className="font-medium">{parsedData.education.degree}</p>
                    <p className="text-gray-600">{parsedData.education.school}</p>
                    <p className="text-gray-600">{parsedData.education.year}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Job Recommendations */}
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
                <TrendingUp className="w-6 h-6 mr-2 text-green-600" />
                Personalized Job Recommendations
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Conservative Tier */}
                <div className="border-2 border-blue-200 rounded-lg p-6">
                  <div className="flex items-center mb-4">
                    <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                      <Star className="w-4 h-4 text-blue-600" />
                    </div>
                    <h3 className="font-semibold text-gray-900">Safe Growth</h3>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="font-medium text-sm">Senior Marketing Coordinator</p>
                      <p className="text-xs text-gray-600">Healthcare Technology Solutions</p>
                      <p className="text-xs text-gray-600">Atlanta, GA</p>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Salary:</span>
                      <span className="font-medium">$58,000 - $62,000</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Match Score:</span>
                      <span className="font-medium text-green-600">92%</span>
                    </div>
                  </div>
                </div>

                {/* Optimal Tier */}
                <div className="border-2 border-purple-200 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-6">
                  <div className="flex items-center mb-4">
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                      <TrendingUp className="w-4 h-4 text-purple-600" />
                    </div>
                    <h3 className="font-semibold text-gray-900">Strategic Advance</h3>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="font-medium text-sm">Digital Marketing Specialist</p>
                      <p className="text-xs text-gray-600">TechStart Atlanta</p>
                      <p className="text-xs text-gray-600">Atlanta, GA (Remote OK)</p>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Salary:</span>
                      <span className="font-medium">$60,000 - $65,000</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Match Score:</span>
                      <span className="font-medium text-green-600">88%</span>
                    </div>
                  </div>
                </div>

                {/* Stretch Tier */}
                <div className="border-2 border-dashed border-orange-200 rounded-lg p-6">
                  <div className="flex items-center mb-4">
                    <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center mr-3">
                      <TrendingUp className="w-4 h-4 text-orange-600" />
                    </div>
                    <h3 className="font-semibold text-gray-900">Ambitious Leap</h3>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="font-medium text-sm">Marketing Manager</p>
                      <p className="text-xs text-gray-600">Consumer Goods Corp</p>
                      <p className="text-xs text-gray-600">Atlanta, GA</p>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Salary:</span>
                      <span className="font-medium">$65,000 - $70,000</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Match Score:</span>
                      <span className="font-medium text-green-600">85%</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex flex-col sm:flex-row gap-4">
                <button
                  onClick={resetForm}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Upload Another Resume
                </button>
                <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  View Full Recommendations
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumeUploadDemo;
