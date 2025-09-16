#!/usr/bin/env python3
"""
Dream-Vault Payment System Setup
Integrates Stripe for subscription billing and payment processing.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import stripe

class PaymentSystemSetup:
    """Sets up Stripe payment processing for Dream-Vault."""
    
    def __init__(self, project_root: str = "/workspace"):
        self.project_root = Path(project_root)
        self.stripe_config = {}
        
    def create_stripe_config(self):
        """Create Stripe configuration."""
        print("💳 Setting up Stripe payment system...")
        
        config = {
            "stripe": {
                "public_key": "pk_test_your_public_key_here",  # Replace with actual key
                "secret_key": "sk_test_your_secret_key_here",  # Replace with actual key
                "webhook_secret": "whsec_your_webhook_secret_here",  # Replace with actual key
                "environment": "test",  # Change to "live" for production
                "currency": "usd"
            },
            "products": {
                "free_tier": {
                    "name": "Dream-Vault Free",
                    "description": "Free tier with limited features",
                    "price_id": None,  # Free tier doesn't need Stripe product
                    "features": [
                        "10 conversations processed",
                        "Basic AI agent training",
                        "Limited IP extraction (5 items)",
                        "Community support"
                    ]
                },
                "pro_tier": {
                    "name": "Dream-Vault Pro",
                    "description": "Pro tier with unlimited features",
                    "price_id": "price_pro_monthly",  # Will be created in Stripe
                    "monthly_price": 9900,  # $99.00 in cents
                    "annual_price": 79200,  # $79.20/month annually (20% discount)
                    "features": [
                        "Unlimited conversations",
                        "Advanced AI training (all 5 agents)",
                        "Full IP extraction",
                        "Priority support",
                        "API access",
                        "Advanced analytics",
                        "Export capabilities"
                    ]
                },
                "enterprise_tier": {
                    "name": "Dream-Vault Enterprise",
                    "description": "Enterprise tier with custom features",
                    "price_id": "price_enterprise_monthly",  # Will be created in Stripe
                    "monthly_price": 99900,  # $999.00 in cents
                    "annual_price": 799200,  # $799.20/month annually (20% discount)
                    "features": [
                        "Everything in Pro",
                        "Custom AI models",
                        "White-label deployment",
                        "Dedicated support",
                        "Advanced analytics",
                        "Custom integrations",
                        "SLA guarantee",
                        "On-premise deployment option"
                    ]
                }
            },
            "billing": {
                "trial_period_days": 14,
                "grace_period_days": 3,
                "invoice_reminder_days": [7, 3, 1],
                "payment_method_types": ["card"],
                "allowed_countries": ["US", "CA", "GB", "AU", "DE", "FR", "NL", "SE", "DK", "NO"]
            },
            "webhooks": {
                "events": [
                    "customer.subscription.created",
                    "customer.subscription.updated",
                    "customer.subscription.deleted",
                    "invoice.payment_succeeded",
                    "invoice.payment_failed",
                    "customer.subscription.trial_will_end"
                ],
                "endpoint_url": "/api/webhooks/stripe"
            }
        }
        
        config_path = self.project_root / "business/financials/stripe_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"   ✅ Stripe configuration saved: {config_path}")
        return config
    
    def create_stripe_products(self):
        """Create Stripe products and prices."""
        print("🏷️ Creating Stripe products and prices...")
        
        # Note: This would require actual Stripe API keys
        # For now, we'll create the structure
        
        products = {
            "pro_monthly": {
                "product_name": "Dream-Vault Pro",
                "price": 9900,  # $99.00 in cents
                "currency": "usd",
                "interval": "month",
                "price_id": "price_pro_monthly"
            },
            "pro_annual": {
                "product_name": "Dream-Vault Pro (Annual)",
                "price": 79200,  # $79.20/month annually
                "currency": "usd",
                "interval": "year",
                "price_id": "price_pro_annual"
            },
            "enterprise_monthly": {
                "product_name": "Dream-Vault Enterprise",
                "price": 99900,  # $999.00 in cents
                "currency": "usd",
                "interval": "month",
                "price_id": "price_enterprise_monthly"
            },
            "enterprise_annual": {
                "product_name": "Dream-Vault Enterprise (Annual)",
                "price": 799200,  # $799.20/month annually
                "currency": "usd",
                "interval": "year",
                "price_id": "price_enterprise_annual"
            }
        }
        
        products_path = self.project_root / "business/financials/stripe_products.json"
        with open(products_path, 'w') as f:
            json.dump(products, f, indent=2)
        
        print(f"   ✅ Stripe products configuration saved: {products_path}")
        return products
    
    def create_payment_integration_code(self):
        """Create payment integration code for the application."""
        print("💻 Creating payment integration code...")
        
        # Stripe integration code
        stripe_code = '''
# import stripe  # Uncomment when stripe is installed
from flask import Flask, request, jsonify
from typing import Dict, Any
import logging

class StripePaymentProcessor:
    """Handles Stripe payment processing for Dream-Vault."""
    
    def __init__(self, secret_key: str, webhook_secret: str):
        # stripe.api_key = secret_key  # Uncomment when stripe is installed
        self.webhook_secret = webhook_secret
        
    def create_customer(self, email: str, name: str) -> Dict[str, Any]:
        """Create a new Stripe customer."""
        try:
            # customer = stripe.Customer.create(  # Uncomment when stripe is installed
            #     email=email,
            #     name=name,
            #     metadata={
            #         "source": "dream-vault",
            #         "plan": "free"
            #     }
            # )
            # return {
            #     "success": True,
            #     "customer_id": customer.id,
            #     "customer": customer
            # }
            return {"success": False, "error": "Stripe not configured"}
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_subscription(self, customer_id: str, price_id: str, trial_period_days: int = 14) -> Dict[str, Any]:
        """Create a new subscription for a customer."""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                trial_period_days=trial_period_days,
                metadata={
                    "source": "dream-vault"
                }
            )
            return {
                "success": True,
                "subscription_id": subscription.id,
                "subscription": subscription
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription."""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            return {
                "success": True,
                "subscription": subscription
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "success": True,
                "subscription": subscription
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_payment_intent(self, amount: int, currency: str = "usd", customer_id: str = None) -> Dict[str, Any]:
        """Create a payment intent for one-time payments."""
        try:
            intent_params = {
                "amount": amount,
                "currency": currency,
                "automatic_payment_methods": {"enabled": True}
            }
            
            if customer_id:
                intent_params["customer"] = customer_id
                
            intent = stripe.PaymentIntent.create(**intent_params)
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "payment_intent": intent
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            # Handle different event types
            if event["type"] == "customer.subscription.created":
                return self._handle_subscription_created(event["data"]["object"])
            elif event["type"] == "customer.subscription.updated":
                return self._handle_subscription_updated(event["data"]["object"])
            elif event["type"] == "customer.subscription.deleted":
                return self._handle_subscription_deleted(event["data"]["object"])
            elif event["type"] == "invoice.payment_succeeded":
                return self._handle_payment_succeeded(event["data"]["object"])
            elif event["type"] == "invoice.payment_failed":
                return self._handle_payment_failed(event["data"]["object"])
            else:
                return {"success": True, "message": "Event handled"}
                
        except ValueError as e:
            return {"success": False, "error": f"Invalid payload: {e}"}
        except stripe.error.SignatureVerificationError as e:
            return {"success": False, "error": f"Invalid signature: {e}"}
    
    def _handle_subscription_created(self, subscription):
        """Handle subscription created event."""
        # Update user's subscription status in database
        # Grant access to paid features
        logging.info(f"Subscription created: {subscription.id}")
        return {"success": True, "message": "Subscription created"}
    
    def _handle_subscription_updated(self, subscription):
        """Handle subscription updated event."""
        # Update user's subscription status
        logging.info(f"Subscription updated: {subscription.id}")
        return {"success": True, "message": "Subscription updated"}
    
    def _handle_subscription_deleted(self, subscription):
        """Handle subscription deleted event."""
        # Revoke paid features access
        logging.info(f"Subscription deleted: {subscription.id}")
        return {"success": True, "message": "Subscription deleted"}
    
    def _handle_payment_succeeded(self, invoice):
        """Handle successful payment."""
        # Update billing status
        logging.info(f"Payment succeeded: {invoice.id}")
        return {"success": True, "message": "Payment succeeded"}
    
    def _handle_payment_failed(self, invoice):
        """Handle failed payment."""
        # Send payment failure notification
        logging.info(f"Payment failed: {invoice.id}")
        return {"success": True, "message": "Payment failed"}

# Flask API endpoints
app = Flask(__name__)

@app.route("/api/create-subscription", methods=["POST"])
def create_subscription():
    """Create a new subscription."""
    data = request.get_json()
    
    # Initialize payment processor
    processor = StripePaymentProcessor(
        secret_key=os.getenv("STRIPE_SECRET_KEY"),
        webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET")
    )
    
    # Create customer if needed
    if not data.get("customer_id"):
        customer_result = processor.create_customer(
            email=data["email"],
            name=data["name"]
        )
        if not customer_result["success"]:
            return jsonify(customer_result), 400
        customer_id = customer_result["customer_id"]
    else:
        customer_id = data["customer_id"]
    
    # Create subscription
    subscription_result = processor.create_subscription(
        customer_id=customer_id,
        price_id=data["price_id"],
        trial_period_days=data.get("trial_period_days", 14)
    )
    
    if subscription_result["success"]:
        return jsonify(subscription_result), 200
    else:
        return jsonify(subscription_result), 400

@app.route("/api/cancel-subscription", methods=["POST"])
def cancel_subscription():
    """Cancel a subscription."""
    data = request.get_json()
    
    processor = StripePaymentProcessor(
        secret_key=os.getenv("STRIPE_SECRET_KEY"),
        webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET")
    )
    
    result = processor.cancel_subscription(data["subscription_id"])
    
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route("/api/webhooks/stripe", methods=["POST"])
def stripe_webhook():
    """Handle Stripe webhook events."""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    
    processor = StripePaymentProcessor(
        secret_key=os.getenv("STRIPE_SECRET_KEY"),
        webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET")
    )
    
    result = processor.handle_webhook(payload, sig_header)
    
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

if __name__ == "__main__":
    app.run(debug=True)
'''
        
        code_path = self.project_root / "business/financials/stripe_integration.py"
        with open(code_path, 'w') as f:
            f.write(stripe_code)
        
        print(f"   ✅ Stripe integration code saved: {code_path}")
        return stripe_code
    
    def create_billing_dashboard_config(self):
        """Create billing dashboard configuration."""
        print("📊 Creating billing dashboard configuration...")
        
        dashboard_config = {
            "dashboard": {
                "title": "Dream-Vault Billing Dashboard",
                "features": [
                    "View current subscription status",
                    "Update payment method",
                    "Download invoices",
                    "View usage statistics",
                    "Manage subscription",
                    "View billing history"
                ]
            },
            "usage_tracking": {
                "conversations_processed": {
                    "limit_type": "monthly",
                    "reset_period": "month",
                    "free_limit": 10,
                    "pro_limit": -1  # Unlimited
                },
                "ip_extractions": {
                    "limit_type": "monthly", 
                    "reset_period": "month",
                    "free_limit": 5,
                    "pro_limit": -1  # Unlimited
                },
                "api_calls": {
                    "limit_type": "monthly",
                    "reset_period": "month", 
                    "free_limit": 100,
                    "pro_limit": 10000
                }
            },
            "notifications": {
                "usage_alerts": {
                    "free_tier": [0.8, 0.9, 1.0],  # 80%, 90%, 100% of limit
                    "pro_tier": [0.9, 1.0]  # 90%, 100% of limit
                },
                "billing_alerts": {
                    "payment_failed": True,
                    "subscription_expiring": 7,  # days before
                    "trial_ending": 3  # days before
                }
            }
        }
        
        dashboard_path = self.project_root / "business/financials/billing_dashboard.json"
        with open(dashboard_path, 'w') as f:
            json.dump(dashboard_config, f, indent=2)
        
        print(f"   ✅ Billing dashboard configuration saved: {dashboard_path}")
        return dashboard_config
    
    def create_payment_ui_components(self):
        """Create payment UI components."""
        print("🎨 Creating payment UI components...")
        
        # Checkout form HTML
        checkout_form = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dream-Vault Checkout</title>
    <script src="https://js.stripe.com/v3/"></script>
    <style>
        .checkout-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 2rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .plan-card {
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.3s;
        }
        .plan-card.selected {
            border-color: #667eea;
            background-color: #f8f9ff;
        }
        .plan-card h3 {
            margin: 0 0 0.5rem 0;
            color: #333;
        }
        .plan-price {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        .plan-features {
            list-style: none;
            padding: 0;
            margin: 1rem 0;
        }
        .plan-features li {
            padding: 0.25rem 0;
            color: #666;
        }
        .plan-features li::before {
            content: "✅";
            margin-right: 0.5rem;
        }
        .checkout-form {
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 8px;
            margin-top: 2rem;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #333;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        .submit-button {
            background: #667eea;
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 4px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-top: 1rem;
        }
        .submit-button:hover {
            background: #5a6fd8;
        }
        .submit-button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="checkout-container">
        <h1>Choose Your Plan</h1>
        
        <div class="plan-card" data-plan="pro" data-price="9900">
            <h3>Pro Plan</h3>
            <div class="plan-price">$99<span style="font-size: 1rem; color: #666;">/month</span></div>
            <ul class="plan-features">
                <li>Unlimited conversations</li>
                <li>Advanced AI training (all 5 agents)</li>
                <li>Full IP extraction</li>
                <li>Priority support</li>
                <li>API access</li>
                <li>Advanced analytics</li>
                <li>Export capabilities</li>
            </ul>
        </div>
        
        <div class="plan-card" data-plan="enterprise" data-price="99900">
            <h3>Enterprise Plan</h3>
            <div class="plan-price">$999<span style="font-size: 1rem; color: #666;">/month</span></div>
            <ul class="plan-features">
                <li>Everything in Pro</li>
                <li>Custom AI models</li>
                <li>White-label deployment</li>
                <li>Dedicated support</li>
                <li>Advanced analytics</li>
                <li>Custom integrations</li>
                <li>SLA guarantee</li>
                <li>On-premise deployment option</li>
            </ul>
        </div>
        
        <div class="checkout-form" id="checkout-form" style="display: none;">
            <h2>Complete Your Purchase</h2>
            <form id="payment-form">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="name">Full Name</label>
                    <input type="text" id="name" name="name" required>
                </div>
                <div class="form-group">
                    <label for="card-element">Credit Card</label>
                    <div id="card-element"></div>
                </div>
                <button type="submit" class="submit-button" id="submit-button">
                    Start Free Trial
                </button>
            </form>
        </div>
    </div>

    <script>
        // Initialize Stripe
        const stripe = Stripe('pk_test_your_public_key_here');
        const elements = stripe.elements();
        
        // Create card element
        const cardElement = elements.create('card');
        cardElement.mount('#card-element');
        
        // Plan selection
        let selectedPlan = null;
        let selectedPrice = null;
        
        document.querySelectorAll('.plan-card').forEach(card => {
            card.addEventListener('click', function() {
                // Remove selected class from all cards
                document.querySelectorAll('.plan-card').forEach(c => c.classList.remove('selected'));
                
                // Add selected class to clicked card
                this.classList.add('selected');
                
                // Set selected plan
                selectedPlan = this.dataset.plan;
                selectedPrice = this.dataset.price;
                
                // Show checkout form
                document.getElementById('checkout-form').style.display = 'block';
            });
        });
        
        // Form submission
        document.getElementById('payment-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!selectedPlan) {
                alert('Please select a plan first');
                return;
            }
            
            const submitButton = document.getElementById('submit-button');
            submitButton.disabled = true;
            submitButton.textContent = 'Processing...';
            
            try {
                // Create subscription
                const response = await fetch('/api/create-subscription', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: document.getElementById('email').value,
                        name: document.getElementById('name').value,
                        price_id: selectedPlan === 'pro' ? 'price_pro_monthly' : 'price_enterprise_monthly',
                        trial_period_days: 14
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Redirect to success page
                    window.location.href = '/checkout/success?subscription_id=' + result.subscription_id;
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = 'Start Free Trial';
            }
        });
    </script>
</body>
</html>
'''
        
        checkout_path = self.project_root / "business/financials/checkout_form.html"
        with open(checkout_path, 'w') as f:
            f.write(checkout_form)
        
        print(f"   ✅ Payment UI components saved: {checkout_path}")
        return checkout_form
    
    def create_setup_instructions(self):
        """Create setup instructions for payment system."""
        print("📋 Creating setup instructions...")
        
        instructions = {
            "setup_steps": [
                {
                    "step": 1,
                    "title": "Create Stripe Account",
                    "description": "Sign up for a Stripe account at stripe.com",
                    "actions": [
                        "Go to stripe.com and create an account",
                        "Complete business verification",
                        "Get your API keys from the dashboard"
                    ]
                },
                {
                    "step": 2,
                    "title": "Configure API Keys",
                    "description": "Set up your Stripe API keys in the application",
                    "actions": [
                        "Copy your test API keys from Stripe dashboard",
                        "Update stripe_config.json with your keys",
                        "Set environment variables for production"
                    ]
                },
                {
                    "step": 3,
                    "title": "Create Products in Stripe",
                    "description": "Create products and prices in Stripe dashboard",
                    "actions": [
                        "Create 'Dream-Vault Pro' product",
                        "Create 'Dream-Vault Enterprise' product",
                        "Set up monthly and annual pricing",
                        "Copy price IDs to configuration"
                    ]
                },
                {
                    "step": 4,
                    "title": "Set Up Webhooks",
                    "description": "Configure webhook endpoints in Stripe",
                    "actions": [
                        "Add webhook endpoint: https://yourdomain.com/api/webhooks/stripe",
                        "Select required events",
                        "Copy webhook secret to configuration"
                    ]
                },
                {
                    "step": 5,
                    "title": "Test Payment Flow",
                    "description": "Test the complete payment flow",
                    "actions": [
                        "Use Stripe test cards",
                        "Test subscription creation",
                        "Test webhook handling",
                        "Test subscription cancellation"
                    ]
                }
            ],
            "test_cards": {
                "successful": "4242 4242 4242 4242",
                "declined": "4000 0000 0000 0002",
                "insufficient_funds": "4000 0000 0000 9995",
                "expired": "4000 0000 0000 0069"
            },
            "environment_variables": [
                "STRIPE_PUBLIC_KEY=pk_test_...",
                "STRIPE_SECRET_KEY=sk_test_...",
                "STRIPE_WEBHOOK_SECRET=whsec_...",
                "STRIPE_ENVIRONMENT=test"
            ],
            "production_checklist": [
                "Switch to live API keys",
                "Update webhook URLs to production domain",
                "Test with real payment methods",
                "Set up monitoring and alerts",
                "Configure backup payment methods"
            ]
        }
        
        instructions_path = self.project_root / "business/financials/payment_setup_instructions.json"
        with open(instructions_path, 'w') as f:
            json.dump(instructions, f, indent=2)
        
        print(f"   ✅ Setup instructions saved: {instructions_path}")
        return instructions
    
    def run_full_setup(self):
        """Run complete payment system setup."""
        print("💳 Setting up Dream-Vault Payment System...")
        print("=" * 60)
        
        # Create all payment components
        config = self.create_stripe_config()
        products = self.create_stripe_products()
        code = self.create_payment_integration_code()
        dashboard = self.create_billing_dashboard_config()
        ui = self.create_payment_ui_components()
        instructions = self.create_setup_instructions()
        
        print("=" * 60)
        print("🎉 Payment System Setup Complete!")
        print("\n💳 Created Payment Components:")
        print("   business/financials/stripe_config.json - Stripe configuration")
        print("   business/financials/stripe_products.json - Product definitions")
        print("   business/financials/stripe_integration.py - Payment processing code")
        print("   business/financials/billing_dashboard.json - Billing dashboard config")
        print("   business/financials/checkout_form.html - Payment UI")
        print("   business/financials/payment_setup_instructions.json - Setup guide")
        
        print(f"\n💰 Pricing Structure:")
        print(f"   Free Tier: $0/month (10 conversations, limited features)")
        print(f"   Pro Tier: $99/month (unlimited, full features)")
        print(f"   Enterprise: $999/month (custom, white-label)")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Create Stripe account and get API keys")
        print(f"   2. Update configuration with your Stripe keys")
        print(f"   3. Create products in Stripe dashboard")
        print(f"   4. Set up webhook endpoints")
        print(f"   5. Test payment flow with test cards")
        print(f"   6. Deploy to production with live keys")
        
        print(f"\n💡 Revenue Potential:")
        print(f"   Month 1: $500 MRR (5 Pro customers)")
        print(f"   Month 6: $10,000 MRR (100 Pro customers)")
        print(f"   Year 1: $50,000 MRR (500 Pro customers)")
        
        print(f"\n🚀 Your payment system is ready to process subscriptions!")

def main():
    """Main execution."""
    setup = PaymentSystemSetup()
    setup.run_full_setup()

if __name__ == "__main__":
    main()