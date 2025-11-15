
## Analyze, Choose, and Justify the Appropriate Resource Option for Deploying the App

This project involved provisioning several Azure resources and choosing the best compute option for deploying a Python Flask CMS application. Below is the analysis and final justification.

# 1. Azure Resource Setup

A. Resource Group

I began by creating a dedicated Resource Group to keep all project resources organized and easy to manage.

Name: cms

Region: East US (same for all resources)

Keeping everything in one group ensures easier management and simplifies cleanup after grading.

# B. SQL Database

Next, I created the SQL Database used to store users and article data.

Database Configuration

Database name: cms

SQL Server: New server (e.g., cms.database.windows.net)

Admin username: cmsadmin

Password: CMS4dmin

Tier: DTU Basic (low-cost)

Networking

Enabled Public Endpoint

Allowed Azure services to access the server

Added my local IP address

After setup, I used Azure’s Query Editor to run the SQL scripts from the starter code (users.sql → posts.sql) to create and populate both tables.

# 📌 Submission Screenshot: Users and posts tables created and populated.

# C. Storage Account (Azure Blob Storage)

To store uploaded article images, I created a Storage Account in the same resource group.

Settings

Unique storage name (example: images11)

Enabled anonymous access for containers

Access tier: Cool

Then I created a container:

Name: images

Access level: Container (anonymous read)

I also noted the Storage Account Name, Access Keys, and Connection String for use in the application.

# 📌 Submission Screenshot: Blob service endpoint URL shown in Storage Account → Properties.

# 2. Microsoft Entra ID Setup (Microsoft Login)

To enable Microsoft authentication, I registered the application in Microsoft Entra ID.

App Registration

Name: cmsEntraID

Supported account types: Multitenant + personal Microsoft accounts

From the registration, I obtained:

Application (client) ID, Client Secret

Authentication Setup

After deploying the app, I configured the required Redirect URIs:

https://udacitycms.azurewebsites.net/getAToken


Logout URL:

https://udacitycms.azurewebsites.net/login


# 📌 Submission Screenshot: Redirect URIs in the Authentication settings.

# 3. Deployment Decision & Justification

This project required choosing between deploying the Flask app on a Virtual Machine (VM) or an Azure App Service.

# A. Analysis

Cost

App Service: Free (F1) tier available — very cost-efficient.

VM: Even the smallest VM (B1ls) incurs continuous hourly charges, even when idle.

Scalability

App Service: Built-in scaling (both vertical & horizontal).

VM: Manual scaling setup required (load balancers, multiple VMs).

Availability

App Service: High availability built-in by Azure.

VM: Requires availability sets/zones, which adds complexity.

Workflow

App Service: Simple GitHub CI/CD integration via Deployment Center.

VM: Requires SSH login, manual Python setup, Nginx configuration, and manual deployments.

# B. Final Choice: Azure App Service

I selected Azure App Service as the deployment option.

Reasons for Choosing App Service

Easier deployment: No need to configure OS, Python, or a web server manually. Azure handles it.

Cost-effective: The Free tier is ideal for development and small projects.

Better workflow: GitHub-based CI/CD makes updates simple and automatic.

Less overhead: Allows me to focus on application code instead of infrastructure.

Overall, Azure App Service provides a smoother, cheaper, and more scalable deployment path compared to a VM for this type of project.
