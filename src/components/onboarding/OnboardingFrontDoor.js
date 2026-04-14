import React, { useState } from 'react';

const PHASE_A_QUESTIONS = [
  {
    id: 'institution_name',
    question: 'What is the name of the institution where I am deployed?',
    placeholder: 'Enter institution name',
    helperText: 'e.g., City General Hospital, Acme Corp.',
    validationError: 'Institution name cannot be empty.',
  },
  {
    id: 'institution_type',
    question: 'What type of institution is this? (e.g., hospital, university, corporate office)',
    placeholder: 'Enter institution type',
    helperText: 'Be as specific as possible.',
    validationError: 'Institution type cannot be empty.',
  },
  {
    id: 'primary_operator',
    question: 'Who am I speaking with today? Please provide your name or identifier.',
    placeholder: 'Enter your name or ID',
    helperText: 'This identifies the primary authority.',
    validationError: 'Operator identity is required.',
  },
  {
    id: 'primary_operator_role',
    question: 'What is your role within this institution?',
    placeholder: 'Enter your role',
    helperText: 'e.g., Administrator, Department Head',
    validationError: 'Operator role cannot be empty.',
  },
  {
    id: 'additional_users',
    question: "Are there others who will be using me here? Please list their names or roles, or say 'no'.",
    placeholder: "Enter additional users or 'no'",
    helperText: 'Separate multiple entries with commas.',
    validationError: "Please enter user details or 'no'.",
  },
];

export default function OnboardingFrontDoor() {
  const [step, setStep] = useState('welcome');
  const [answers, setAnswers] = useState({});
  const [inputValue, setInputValue] = useState('');
  const [validationError, setValidationError] = useState('');

  function validateInput(value, question) {
    if (!value.trim()) {
      return question.validationError;
    }
    if (question.id === 'additional_users') {
      if (value.trim().toLowerCase() !== 'no') {
        // Simple check: ensure input is not empty if not 'no'
        return null;
      } else {
        return null;
      }
    }
    return null;
  }

  function onNext() {
    if (step === 'welcome') {
      setStep(0); // Start Phase A questions
      setInputValue('');
      setValidationError('');
      return;
    }

    if (typeof step === 'number') {
      const question = PHASE_A_QUESTIONS[step];
      const error = validateInput(inputValue, question);
      if (error) {
        setValidationError(error);
        return;
      } else {
        setAnswers(prev => ({ ...prev, [question.id]: inputValue.trim() }));
        setValidationError('');
        const nextStep = step + 1;
        if (nextStep < PHASE_A_QUESTIONS.length) {
          setStep(nextStep);
          setInputValue(answers[PHASE_A_QUESTIONS[nextStep].id] || '');
        } else {
          setStep('review');
          setInputValue('');
        }
      }
    } else if (step === 'review') {
      // Final confirmation (Phase A done)
      // Persist answers or signal completion (simulate)
      alert('Phase A Onboarding Completed. Data saved.');
    }
  }

  function onBack() {
    if (step === 'welcome') return;
    if (step === 'review') {
      setStep(PHASE_A_QUESTIONS.length - 1);
      setInputValue(answers[PHASE_A_QUESTIONS[PHASE_A_QUESTIONS.length - 1].id] || '');
    } else if (typeof step === 'number') {
      const prevStep = step - 1;
      if (prevStep < 0) {
        setStep('welcome');
        setInputValue('');
        setValidationError('');
      } else {
        setStep(prevStep);
        setInputValue(answers[PHASE_A_QUESTIONS[prevStep].id] || '');
        setValidationError('');
      }
    }
  }

  function renderContent() {
    if (step === 'welcome') {
      return (
        <>
          <h1>Welcome to WESLR Onboarding</h1>
          <p>This guided setup will help align me with your institution&apos;s identity, mission, and safety protocols.</p>
          <button onClick={onNext}>Start Here</button>
          <div style={{ marginTop: '20px' }}>
            <button>Sign In</button>
            <button style={{ marginLeft: '10px' }}>Privacy / License</button>
            <button style={{ float: 'right' }}>Enable Voice</button>
          </div>
        </>
      );
    }

    if (typeof step === 'number') {
      const question = PHASE_A_QUESTIONS[step];
      return (
        <div>
          <label htmlFor="inputField"><strong>{question.question}</strong></label>
          <input
            id="inputField"
            type="text"
            autoFocus
            placeholder={question.placeholder}
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            style={{ fontFamily: 'monospace', borderBottom: '2px solid black', padding: '5px', outline: 'none' }}
          />
          <div style={{ color: 'gray', fontSize: '0.9em' }}>{question.helperText}</div>
          {validationError && <div style={{ color: 'red' }}>{validationError}</div>}
          <div style={{ marginTop: '15px' }}>
            <button onClick={onBack} disabled={step === 0}>Back</button>
            <button onClick={onNext} style={{ float: 'right' }}>Next</button>
          </div>
        </div>
      );
    }

    if (step === 'review') {
      return (
        <div>
          <h2>Review Your Onboarding Information</h2>
          <p>Please confirm the details you have provided. You can use the Back button to make any changes.</p>

          <ul>
            {PHASE_A_QUESTIONS.map(q => (
              <li key={q.id}>
                <strong>{q.question}</strong><br />{answers[q.id] || 'Not answered'}
              </li>
            ))}
          </ul>
          <div style={{ color: 'darkred', marginTop: '10px' }}>
            Final confirmation binds governance and will restrict core modifications without explicit authorization.
          </div>
          <div style={{ marginTop: '15px' }}>
            <button onClick={onBack}>Back</button>
            <button onClick={onNext} style={{ float: 'right' }}>Confirm and Complete Onboarding</button>
          </div>
        </div>
      );
    }
  }

  return (
    <div style={{ maxWidth: 600, margin: '40px auto', backgroundColor: 'white', color: 'black', padding: 20, fontFamily: 'Arial, sans-serif', textAlign: 'center' }}>
      {renderContent()}
    </div>
  );
}
