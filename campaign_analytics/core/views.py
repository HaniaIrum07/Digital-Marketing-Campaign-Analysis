from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponse, FileResponse
import pandas as pd
import os
import json
import joblib
from django.conf import settings
from reportlab.pdfgen import canvas
import io
from django.contrib.auth import authenticate, login as auth_login

def custom_login(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            if user.groups.filter(name='Admin').exists():
                return redirect('admin_dashboard')
            elif user.groups.filter(name='Manager').exists():
                return redirect('manager_dashboard')
            elif user.groups.filter(name='Client').exists():
                return redirect('client_dashboard')
            else:
                return redirect('home')
        else:
            error = "Invalid username or password."
    return render(request, 'core/login.html', {'error': error})

# Load models once when the server starts
MODEL_DIR = os.path.join(settings.BASE_DIR.parent, 'model')
gb_model = joblib.load(os.path.join(MODEL_DIR, 'gb_classifier.pkl'))
gb_reg = joblib.load(os.path.join(MODEL_DIR, 'gb_regressor.pkl'))
scaler_clf = joblib.load(os.path.join(MODEL_DIR, 'scaler_classifier.pkl'))
scaler_reg = joblib.load(os.path.join(MODEL_DIR, 'scaler_regressor.pkl'))

FEATURE_COLUMNS = [
    'Age', 'Income', 'AdSpend', 'ClickThroughRate', 'WebsiteVisits',
    'PagesPerVisit', 'TimeOnSite', 'SocialShares', 'EmailOpens', 'EmailClicks',
    'PreviousPurchases', 'LoyaltyPoints', 'Gender_Male',
    'CampaignChannel_PPC', 'CampaignChannel_Referral', 'CampaignChannel_SEO', 'CampaignChannel_Social Media',
    'CampaignType_Consideration', 'CampaignType_Conversion', 'CampaignType_Retention'
]


def home(request):
    return HttpResponse("<h1>Marketing Campaign Analytics</h1><p>Django is connected and working.</p>")


@login_required
def admin_dashboard(request):
    if not request.user.groups.filter(name='Admin').exists():
        return redirect('unauthorized')

    csv_path = os.path.join(settings.BASE_DIR.parent, 'digital_marketing_campaign_dataset.csv')
    df = pd.read_csv(csv_path)

    total_customers = len(df)
    total_converted = int(df['Conversion'].sum())
    total_not_converted = total_customers - total_converted
    avg_conversion_rate = round(df['ConversionRate'].mean(), 4)

    channel_data = df.groupby('CampaignChannel')['Conversion'].mean().round(4)
    channel_labels = json.dumps(list(channel_data.index))
    channel_values = json.dumps([float(v) for v in channel_data.values])

    context = {
        'username': request.user.username,
        'total_customers': total_customers,
        'total_converted': total_converted,
        'total_not_converted': total_not_converted,
        'avg_conversion_rate': avg_conversion_rate,
        'channel_labels': channel_labels,
        'channel_values': channel_values,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def predict_view(request):
    if not request.user.groups.filter(name__in=['Admin', 'Manager']).exists():
        return redirect('unauthorized')

    result = None

    if request.method == 'POST':
        input_data = {col: 0 for col in FEATURE_COLUMNS}

        input_data['Age'] = float(request.POST.get('age'))
        input_data['Income'] = float(request.POST.get('income'))
        input_data['AdSpend'] = float(request.POST.get('adspend'))
        input_data['ClickThroughRate'] = float(request.POST.get('ctr'))
        input_data['WebsiteVisits'] = float(request.POST.get('website_visits'))
        input_data['PagesPerVisit'] = float(request.POST.get('pages_per_visit'))
        input_data['TimeOnSite'] = float(request.POST.get('time_on_site'))
        input_data['SocialShares'] = float(request.POST.get('social_shares'))
        input_data['EmailOpens'] = float(request.POST.get('email_opens'))
        input_data['EmailClicks'] = float(request.POST.get('email_clicks'))
        input_data['PreviousPurchases'] = float(request.POST.get('previous_purchases'))
        input_data['LoyaltyPoints'] = float(request.POST.get('loyalty_points'))

        gender = request.POST.get('gender')
        if gender == 'Male':
            input_data['Gender_Male'] = 1

        channel = request.POST.get('channel')
        if channel in ['PPC', 'Referral', 'SEO', 'Social Media']:
            input_data[f'CampaignChannel_{channel}'] = 1

        campaign_type = request.POST.get('campaign_type')
        if campaign_type in ['Consideration', 'Conversion', 'Retention']:
            input_data[f'CampaignType_{campaign_type}'] = 1

        input_df = pd.DataFrame([input_data])[FEATURE_COLUMNS]

        input_scaled_clf = scaler_clf.transform(input_df)
        prediction = gb_model.predict(input_scaled_clf)[0]
        probability = gb_model.predict_proba(input_scaled_clf)[0][1]

        input_scaled_reg = scaler_reg.transform(input_df)
        expected_rate = gb_reg.predict(input_scaled_reg)[0]

        result = {
            'prediction': 'Convert' if prediction == 1 else 'Not Convert',
            'probability': round(probability * 100, 2),
            'expected_rate': round(expected_rate, 4),
        }

        # Save to session so the download view can access it
        request.session['last_prediction'] = result

    return render(request, 'core/predict.html', {'result': result})


@login_required
def download_report(request):
    result = request.session.get('last_prediction')
    if not result:
        return redirect('predict')

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Campaign Prediction Report")

    c.setFont("Helvetica", 12)
    c.drawString(100, 710, f"Generated by: {request.user.username}")
    c.drawString(100, 690, f"Prediction: {result['prediction']}")
    c.drawString(100, 670, f"Conversion Probability: {result['probability']}%")
    c.drawString(100, 650, f"Expected Conversion Rate: {result['expected_rate']}")

    c.save()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename='campaign_prediction_report.pdf')


@login_required
def manager_dashboard(request):
    if not request.user.groups.filter(name='Manager').exists():
        return redirect('unauthorized')

    # Simulated scope: this manager oversees these specific channels
    assigned_channels = ['Email', 'Social Media']

    csv_path = os.path.join(settings.BASE_DIR.parent, 'digital_marketing_campaign_dataset.csv')
    df = pd.read_csv(csv_path)

    # Filter to only this manager's assigned channels
    scoped_df = df[df['CampaignChannel'].isin(assigned_channels)]

    total_customers = len(scoped_df)
    total_converted = int(scoped_df['Conversion'].sum())
    total_not_converted = total_customers - total_converted
    avg_conversion_rate = round(scoped_df['ConversionRate'].mean(), 4)

    channel_data = scoped_df.groupby('CampaignChannel')['Conversion'].mean().round(4)
    channel_labels = json.dumps(list(channel_data.index))
    channel_values = json.dumps([float(v) for v in channel_data.values])

    context = {
        'username': request.user.username,
        'assigned_channels': ', '.join(assigned_channels),
        'total_customers': total_customers,
        'total_converted': total_converted,
        'total_not_converted': total_not_converted,
        'avg_conversion_rate': avg_conversion_rate,
        'channel_labels': channel_labels,
        'channel_values': channel_values,
    }
    return render(request, 'core/manager_dashboard.html', context)


@login_required
def client_dashboard(request):
    if not request.user.groups.filter(name='Client').exists():
        return redirect('unauthorized')

    csv_path = os.path.join(settings.BASE_DIR.parent, 'digital_marketing_campaign_dataset.csv')
    df = pd.read_csv(csv_path)

    # Simulated: this client is linked to the first customer in the dataset
    assigned_customer_id = int(df['CustomerID'].iloc[0])

    customer_row = df[df['CustomerID'] == assigned_customer_id].iloc[0]
    # ... rest of the function stays exactly the same
    # Build input for prediction using this customer's actual data
    input_data = {col: 0 for col in FEATURE_COLUMNS}
    input_data['Age'] = float(customer_row['Age'])
    input_data['Income'] = float(customer_row['Income'])
    input_data['AdSpend'] = float(customer_row['AdSpend'])
    input_data['ClickThroughRate'] = float(customer_row['ClickThroughRate'])
    input_data['WebsiteVisits'] = float(customer_row['WebsiteVisits'])
    input_data['PagesPerVisit'] = float(customer_row['PagesPerVisit'])
    input_data['TimeOnSite'] = float(customer_row['TimeOnSite'])
    input_data['SocialShares'] = float(customer_row['SocialShares'])
    input_data['EmailOpens'] = float(customer_row['EmailOpens'])
    input_data['EmailClicks'] = float(customer_row['EmailClicks'])
    input_data['PreviousPurchases'] = float(customer_row['PreviousPurchases'])
    input_data['LoyaltyPoints'] = float(customer_row['LoyaltyPoints'])

    if customer_row['Gender'] == 'Male':
        input_data['Gender_Male'] = 1
    if customer_row['CampaignChannel'] in ['PPC', 'Referral', 'SEO', 'Social Media']:
        input_data[f"CampaignChannel_{customer_row['CampaignChannel']}"] = 1
    if customer_row['CampaignType'] in ['Consideration', 'Conversion', 'Retention']:
        input_data[f"CampaignType_{customer_row['CampaignType']}"] = 1

    input_df = pd.DataFrame([input_data])[FEATURE_COLUMNS]

    input_scaled_clf = scaler_clf.transform(input_df)
    prediction = gb_model.predict(input_scaled_clf)[0]
    probability = gb_model.predict_proba(input_scaled_clf)[0][1]

    context = {
        'username': request.user.username,
        'customer_id': assigned_customer_id,
        'age': int(customer_row['Age']),
        'income': customer_row['Income'],
        'adspend': customer_row['AdSpend'],
        'channel': customer_row['CampaignChannel'],
        'campaign_type': customer_row['CampaignType'],
        'actual_conversion': 'Converted' if customer_row['Conversion'] == 1 else 'Not Converted',
        'predicted': 'Convert' if prediction == 1 else 'Not Convert',
        'probability': round(probability * 100, 2),
    }
    return render(request, 'core/client_dashboard.html', context)


def unauthorized(request):
    return HttpResponse("<h1>403 - Unauthorized</h1><p>You don't have permission to view this page.</p>")
def custom_logout(request):
    logout(request)
    return redirect('login')