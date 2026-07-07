import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import GoalForm from './GoalForm';

const ALL_GOAL_TYPES = [
  'home_purchase',
  'car_purchase',
  'apartment_move',
  'baby',
  'business',
];

async function selectGoalType(user, goalTypeId) {
  await user.selectOptions(screen.getByLabelText(/select goal type/i), goalTypeId);
}

async function fillHomePurchaseForm(user) {
  await user.clear(screen.getByLabelText(/target home price/i));
  await user.type(screen.getByLabelText(/target home price/i), '400000');
  await user.clear(screen.getByLabelText(/timeline/i));
  await user.type(screen.getByLabelText(/timeline/i), '5');
}

async function fillCarPurchaseForm(user) {
  await user.clear(screen.getByLabelText(/target car price/i));
  await user.type(screen.getByLabelText(/target car price/i), '30000');
  await user.clear(screen.getByLabelText(/timeline/i));
  await user.type(screen.getByLabelText(/timeline/i), '2');
}

async function fillApartmentForm(user) {
  await user.clear(screen.getByLabelText(/target monthly rent/i));
  await user.type(screen.getByLabelText(/target monthly rent/i), '2500');
  await user.clear(screen.getByLabelText(/timeline/i));
  await user.type(screen.getByLabelText(/timeline/i), '12');
}

async function fillBabyForm(user) {
  await user.clear(screen.getByLabelText(/preparation budget/i));
  await user.type(screen.getByLabelText(/preparation budget/i), '15000');
  await user.clear(screen.getByLabelText(/timeline/i));
  await user.type(screen.getByLabelText(/timeline/i), '2');
}

async function fillBusinessForm(user) {
  await user.clear(screen.getByLabelText(/initial investment/i));
  await user.type(screen.getByLabelText(/initial investment/i), '50000');
  await user.clear(screen.getByLabelText(/monthly operating cost/i));
  await user.type(screen.getByLabelText(/monthly operating cost/i), '4000');
  await user.clear(screen.getByLabelText(/timeline/i));
  await user.type(screen.getByLabelText(/timeline/i), '3');
}

describe('GoalForm', () => {
  it('renders goal type options from goalTypes prop', () => {
    render(<GoalForm onSubmit={jest.fn()} goalTypes={['home_purchase', 'car_purchase']} />);

    expect(screen.getByRole('option', { name: 'Buy a Home' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Buy a Car' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'Have a Baby' })).not.toBeInTheDocument();
  });

  it('populates default values when a goal type is selected', async () => {
    const user = userEvent.setup();
    render(<GoalForm onSubmit={jest.fn()} goalTypes={ALL_GOAL_TYPES} />);

    await selectGoalType(user, 'home_purchase');

    expect(screen.getByLabelText(/down payment/i)).toHaveValue('20');
    expect(screen.getByLabelText(/timeline/i)).toHaveValue('5');
  });

  it('formats currency fields as the user types', async () => {
    const user = userEvent.setup();
    render(<GoalForm onSubmit={jest.fn()} goalTypes={ALL_GOAL_TYPES} />);

    await selectGoalType(user, 'home_purchase');
    const priceInput = screen.getByLabelText(/target home price/i);
    await user.type(priceInput, '400000');

    await waitFor(() => {
      expect(priceInput).toHaveValue('400,000');
    });
  });

  it('keeps submit disabled until required fields are valid', async () => {
    const user = userEvent.setup();
    const onSubmit = jest.fn();
    render(<GoalForm onSubmit={onSubmit} goalTypes={ALL_GOAL_TYPES} />);

    await selectGoalType(user, 'home_purchase');

    const submitButton = screen.getByRole('button', { name: /analyze my path/i });
    expect(submitButton).toBeDisabled();

    await fillHomePurchaseForm(user);

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it.each([
    ['home_purchase', fillHomePurchaseForm, (goal) => {
      expect(goal.type).toBe('home_purchase');
      expect(goal.parameters.homePrice).toBe(400000);
      expect(goal.timeline).toBe(5);
    }],
    ['car_purchase', fillCarPurchaseForm, (goal) => {
      expect(goal.type).toBe('car_purchase');
      expect(goal.parameters.carPrice).toBe(30000);
      expect(goal.timeline).toBe(2);
    }],
    ['apartment_move', fillApartmentForm, (goal) => {
      expect(goal.type).toBe('apartment_move');
      expect(goal.parameters.monthlyRent).toBe(2500);
      expect(goal.timeline).toBe(1);
    }],
    ['baby', fillBabyForm, (goal) => {
      expect(goal.type).toBe('baby');
      expect(goal.parameters.preparationCost).toBe(15000);
      expect(goal.timeline).toBe(2);
    }],
    ['business', fillBusinessForm, (goal) => {
      expect(goal.type).toBe('business');
      expect(goal.parameters.initialInvestment).toBe(50000);
      expect(goal.parameters.monthlyCost).toBe(4000);
      expect(goal.timeline).toBe(3);
    }],
  ])('submits a valid %s goal', async (goalType, fillForm, assertGoal) => {
    const user = userEvent.setup();
    const onSubmit = jest.fn();
    render(<GoalForm onSubmit={onSubmit} goalTypes={ALL_GOAL_TYPES} />);

    await selectGoalType(user, goalType);
    await fillForm(user);
    await user.click(screen.getByRole('button', { name: /analyze my path/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });

    assertGoal(onSubmit.mock.calls[0][0]);
  });

  it('shows a readable summary before submit', async () => {
    const user = userEvent.setup();
    render(<GoalForm onSubmit={jest.fn()} goalTypes={ALL_GOAL_TYPES} />);

    await selectGoalType(user, 'home_purchase');
    await fillHomePurchaseForm(user);

    expect(await screen.findByText(/buy a home for \$400,000/i)).toBeInTheDocument();
  });

  it('prefills from defaultValues when editing an existing goal', async () => {
    render(
      <GoalForm
        onSubmit={jest.fn()}
        goalTypes={ALL_GOAL_TYPES}
        defaultValues={{
          type: 'car_purchase',
          parameters: { carPrice: 28000 },
          timeline: 2,
        }}
      />,
    );

    expect(screen.getByLabelText(/target car price/i)).toHaveValue('28,000');
    expect(screen.getByLabelText(/timeline/i)).toHaveValue('2');
  });

  it('disables submit and shows loading state while analyzing', async () => {
    const user = userEvent.setup();
    render(
      <GoalForm
        onSubmit={jest.fn()}
        goalTypes={ALL_GOAL_TYPES}
        isSubmitting
      />,
    );

    await selectGoalType(user, 'home_purchase');
    await fillHomePurchaseForm(user);

    const submitButton = screen.getByRole('button', { name: /analyze my path/i });
    expect(submitButton).toBeDisabled();
    expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
  });
});
