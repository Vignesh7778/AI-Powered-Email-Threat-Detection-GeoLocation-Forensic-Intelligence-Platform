import os

sample_dir = r'c:\Users\vigne\Desktop\SIH2026\SIH_Proj\AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform Project\datasets\sample_emails'
os.makedirs(sample_dir, exist_ok=True)

# 1. Legitimate EML
legit_eml = '''Received: from mail-relay.google.com (mail-relay.google.com [209.85.220.41])
    by mx.company.org with ESMTP id ABC123XYZ;
    Fri, 28 Aug 2026 08:30:00 +0000
Authentication-Results: mx.company.org; spf=pass smtp.mailfrom=google.com; dkim=pass header.d=google.com; dmarc=pass
From: Google Security Team <no-reply@google.com>
To: analyst@org.gov
Subject: Security Notification: New sign-in on Windows Device
Message-ID: <legit-msg-001@google.com>
Return-Path: <no-reply@google.com>
Date: Fri, 28 Aug 2026 08:30:00 +0000
Content-Type: text/plain; charset="utf-8"

Hi Analyst,

Your Google Account was just accessed from a new Windows device in New Delhi, India.
If this was you, no further action is needed. You can review your active devices at https://myaccount.google.com/device-activity anytime.

Best regards,
Google Account Protection Team
'''

# 2. Phishing EML
phishing_eml = '''Received: from unknown-host.net (unknown-host.net [185.220.101.5])
    by gateway.company.org with SMTP id PHISH999;
    Fri, 28 Aug 2026 09:15:00 +0000
Authentication-Results: gateway.company.org; spf=fail smtp.mailfrom=secure-paypal-login.xyz; dkim=none; dmarc=fail
From: "PayPal Account Security" <service@secure-paypal-login.xyz>
Reply-To: security-alert@secure-paypal-login.xyz
To: victim@company.org
Subject: URGENT: Your PayPal Account Has Been Suspended!
Message-ID: <phish-9912@attacker.net>
Return-Path: <bounce@secure-paypal-login.xyz>
Date: Fri, 28 Aug 2026 09:15:00 +0000
Content-Type: text/html; charset="utf-8"

<html>
<body>
<p>Dear Customer,</p>
<p><b>ACTION REQUIRED:</b> We detected unauthorized sign-in attempts on your account. Your account will be suspended within 24 hours unless you re-authenticate immediately.</p>
<p>Please <a href="http://198.51.100.24/auth/paypal-login.php">Click Here to Verify Your Account Credentials</a> now.</p>
<p>Thank you,<br/>PayPal Support</p>
</body>
</html>
'''

# 3. BEC Wire Fraud EML
bec_eml = '''Received: from mail.vdsina-server.ru (mail.vdsina-server.ru [45.142.214.10])
    by edge.company.org with ESMTP id BEC777;
    Fri, 28 Aug 2026 10:00:00 +0000
Authentication-Results: edge.company.org; spf=fail; dkim=none; dmarc=fail
From: "Robert Vance, CEO" <ceo.desk.vance@gmail.com>
Reply-To: executive.desk2026@gmail.com
To: finance-director@company.org
Subject: Urgent: Confidential Wire Transfer Needed Before 2 PM
Message-ID: <bec-exec-442@mail-spoof.org>
Return-Path: <ceo.desk.vance@gmail.com>
Date: Fri, 28 Aug 2026 10:00:00 +0000
Content-Type: text/plain; charset="utf-8"

Are you at your desk?

I am currently in an executive board meeting and cannot take calls right now. Please handle this discreetly and keep this strictly confidential.
We need to process an immediate wire transfer for an acquisition milestone before the cutoff.

Please send the updated bank routing number and wire transfer instructions for ,000 to the beneficiary vendor account below:
Beneficiary: Apex Strategic Holdings Ltd
Swift Code: CHASUS33XXX
Account: 9482710492

Confirm as soon as the transfer funds have been remitted.

Sent from my iPhone
'''

# 4. Lookalike Impersonation EML
impersonation_eml = '''Received: from host-relay.ro (host-relay.ro [203.0.113.42])
    by mailgate.company.org with ESMTP id IMP333;
    Fri, 28 Aug 2026 11:20:00 +0000
Authentication-Results: mailgate.company.org; spf=fail smtp.mailfrom=paypa1.com; dkim=none; dmarc=fail
From: "PayPal Billing Department" <billing-notice@paypa1.com>
Reply-To: support@paypa1.com
To: accounts@company.org
Subject: Important Notice: Account Statement Invoice #84920
Message-ID: <imp-msg-882@paypa1.com>
Return-Path: <noreply@paypa1.com>
Date: Fri, 28 Aug 2026 11:20:00 +0000
Content-Type: text/html; charset="utf-8"

<html>
<body>
<h2>PayPal Order Confirmation</h2>
<p>You sent a payment of .00 USD to Digital Goods Global.</p>
<p>If you did not make this transaction, dispute this invoice immediately: <a href="http://paypa1.com/dispute/resolve">Review Transaction Details</a></p>
</body>
</html>
'''

# 5. Fake Invoice Fraud EML
invoice_eml = '''Received: from server12.cloud-mail.net (server12.cloud-mail.net [198.51.100.24])
    by corporate.inbox.org with ESMTP id INV555;
    Fri, 28 Aug 2026 12:00:00 +0000
Authentication-Results: corporate.inbox.org; spf=softfail; dkim=none; dmarc=fail
From: "QuickBooks Billing Service" <invoicing@corporate-billing-updates.xyz>
To: ap@targetorg.gov
Subject: Overdue Invoice Attached: PO #83921 - Action Required
Message-ID: <inv-fake-123@corporate-billing-updates.xyz>
Return-Path: <invoicing@corporate-billing-updates.xyz>
Date: Fri, 28 Aug 2026 12:00:00 +0000
Content-Type: text/plain; charset="utf-8"

Please find the attached invoice #83921 for services rendered in August 2026.
There is an outstanding balance of ,320.00 that is past due.

Remit payment to our updated bank details within 48 hours to avoid service interruption and late penalties.

Attached file: invoice_details_PO83921.pdf
'''

# 6. Credential Phishing EML
cred_eml = '''Received: from tor-node.exit.org (tor-node.exit.org [185.220.101.5])
    by office365.gateway.org with ESMTP id CRED111;
    Fri, 28 Aug 2026 12:45:00 +0000
Authentication-Results: office365.gateway.org; spf=fail; dkim=none; dmarc=fail
From: "Microsoft 365 Security Alert" <admin-notify@micros0ft-security.xyz>
Reply-To: no-reply@m365-security-alert.net
To: employee@victimorg.gov
Subject: Critical Security Alert: Password Expiry & Mailbox Quota Exceeded
Message-ID: <cred-m365-901@micros0ft-security.xyz>
Return-Path: <admin-notify@micros0ft-security.xyz>
Date: Fri, 28 Aug 2026 12:45:00 +0000
Content-Type: text/html; charset="utf-8"

<html>
<body>
<p><b>Microsoft 365 Alert:</b> Your corporate mailbox quota exceeded limits and your password expires today.</p>
<p>To prevent loss of incoming emails, verify your account and reset your password immediately:</p>
<p><a href="http://185.220.101.5/m365/portal-login.html">Sign in to Review & Update Your Credentials</a></p>
<p>Microsoft Security Center</p>
</body>
</html>
'''

files = {
    'legitimate.eml': legit_eml,
    'phishing.eml': phishing_eml,
    'bec.eml': bec_eml,
    'impersonation.eml': impersonation_eml,
    'invoice_fraud.eml': invoice_eml,
    'credential_phishing.eml': cred_eml
}

for name, content in files.items():
    path = os.path.join(sample_dir, name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Generated synthetic EML sample:', path)
