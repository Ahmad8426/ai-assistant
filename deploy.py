#!/usr/bin/env python
"""
Deployment helper script for AI Assistant
"""

import os
import sys
import subprocess
import webbrowser

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {text} ".center(60, "="))
    print("=" * 60 + "\n")

def run_command(command, cwd=None):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, 
                               capture_output=True, cwd=cwd)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        return None

def deploy_to_render():
    """Deploy to Render"""
    print_header("DEPLOYING TO RENDER")
    
    # Check if logged in to Render CLI
    print("Checking if render-cli is installed...")
    if run_command("pip show render-cli") is None:
        print("Installing render-cli...")
        run_command("pip install render-cli")
    
    # Deploy using render.yaml
    print("Deploying to Render...")
    print("Please visit https://dashboard.render.com/select-repo?type=web to connect your GitHub repository.")
    print("Follow these steps:")
    print("1. Connect your GitHub account if not already connected")
    print("2. Select the 'ai-assistant' repository")
    print("3. Render will detect the render.yaml file and configure your deployment")
    print("4. Click 'Create Web Service'")
    
    # Open Render dashboard
    webbrowser.open("https://dashboard.render.com/select-repo?type=web")
    
    print("\nAfter deployment, set your GOOGLE_API_KEY in the Render dashboard.")

def deploy_to_heroku():
    """Deploy to Heroku"""
    print_header("DEPLOYING TO HEROKU")
    
    # Check if Heroku CLI is installed
    if run_command("heroku --version") is None:
        print("Heroku CLI is not installed. Please install it from: https://devcenter.heroku.com/articles/heroku-cli")
        return
    
    # Check if logged in
    if "not logged in" in run_command("heroku auth:whoami") or "Error" in run_command("heroku auth:whoami"):
        print("You need to log in to Heroku first.")
        run_command("heroku login")
    
    # Create Heroku app if it doesn't exist
    app_name = "ai-assistant-" + os.path.basename(os.getcwd()).lower().replace(" ", "-")
    if run_command(f"heroku apps:info --app {app_name}") is None:
        print(f"Creating Heroku app: {app_name}")
        run_command(f"heroku create {app_name}")
    
    # Set buildpacks
    print("Setting buildpacks...")
    run_command(f"heroku buildpacks:clear --app {app_name}")
    run_command(f"heroku buildpacks:add heroku/python --app {app_name}")
    
    # Set environment variables
    print("Setting environment variables...")
    api_key = input("Enter your Google Gemini API key: ")
    run_command(f'heroku config:set GOOGLE_API_KEY="{api_key}" --app {app_name}')
    run_command(f'heroku config:set SECRET_KEY="$(python -c \'import os; print(os.urandom(24).hex())\')" --app {app_name}')
    
    # Deploy to Heroku
    print("Deploying to Heroku...")
    run_command(f"git push heroku master")
    
    # Open the app
    print("Opening the deployed app...")
    run_command(f"heroku open --app {app_name}")

def deploy_to_pythonanywhere():
    """Deploy to PythonAnywhere"""
    print_header("DEPLOYING TO PYTHONANYWHERE")
    
    print("To deploy to PythonAnywhere:")
    print("1. Sign up for a PythonAnywhere account at https://www.pythonanywhere.com/")
    print("2. Go to the 'Web' tab and click 'Add a new web app'")
    print("3. Choose 'Flask' and the latest Python version")
    print("4. In the 'Files' tab, upload your project files or clone your GitHub repository:")
    print("   $ git clone https://github.com/Ahmad8426/ai-assistant.git")
    print("5. Set up a virtual environment and install dependencies:")
    print("   $ mkvirtualenv --python=/usr/bin/python3.9 myenv")
    print("   $ workon myenv")
    print("   $ pip install -r requirements.txt")
    print("6. Configure your web app to point to your Flask app")
    print("7. Set environment variables in the 'Web' tab under 'WSGI configuration file'")
    
    # Open PythonAnywhere
    webbrowser.open("https://www.pythonanywhere.com/")

def main():
    """Main function"""
    print_header("AI ASSISTANT DEPLOYMENT")
    
    print("Choose a deployment platform:")
    print("1. Render (Recommended)")
    print("2. Heroku")
    print("3. PythonAnywhere")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        deploy_to_render()
    elif choice == "2":
        deploy_to_heroku()
    elif choice == "3":
        deploy_to_pythonanywhere()
    else:
        print("Invalid choice. Please run the script again and select a valid option.")

if __name__ == "__main__":
    main()
