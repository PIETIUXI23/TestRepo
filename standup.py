# standup.py - Daily Standup Generator using Git and Google Gemini AI
# Version: Clean, no icons, easy to explain and maintain

import subprocess
import datetime
import os
import sys
import logging

# --- Suppress noisy logs from Google/gRPC ---
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("grpc").setLevel(logging.ERROR)

# --- Load environment variables and check dependencies ---
try:
    from dotenv import load_dotenv
    load_dotenv()
    has_dotenv = True
except ImportError:
    has_dotenv = False

try:
    import google.generativeai as genai
    has_gemini = True
except ImportError:
    has_gemini = False


def get_commits_from_yesterday():
    """
    Get all Git commit messages from the last 24 hours.
    Returns a list of commit messages (strings).
    If error occurs, returns empty list.
    """
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    since_date = yesterday.strftime("%Y-%m-%d %H:%M:%S")

    try:
        result = subprocess.run([
            'git', 'log',
            f'--since="{since_date}"',
            '--pretty=format:%s'
        ], capture_output=True, text=True, check=True)

        commits = result.stdout.strip().split('\n')
        return [commit for commit in commits if commit]

    except subprocess.CalledProcessError as e:
        print(f"Error running git log: {e}")
        return []
    except FileNotFoundError:
        print("Error: Git is not installed or not found in PATH.")
        return []


def generate_basic_standup_report(commits):
    """
    Generate a basic daily standup report based on commit messages.
    Input: list of commit messages
    Output: formatted string report
    """
    if not commits:
        return "No commits found in the last 24 hours.\n"

    lines = []
    lines.append("Daily Standup Report")
    lines.append(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("Yesterday I worked on:")
    for i, commit in enumerate(commits, 1):
        lines.append(f"  {i}. {commit}")

    lines.append("")
    lines.append("Today I plan to:")
    lines.append("  - Continue working on pending tasks.")
    lines.append("  - Review code, write tests, or deploy as needed.")

    lines.append("")
    lines.append("Blockers (if any):")
    lines.append("  - None at the moment.")

    return "\n".join(lines)


def enhance_report_with_ai(basic_report):
    """
    Use Google Gemini AI to rewrite the report in a more professional tone.
    Input: basic report (string)
    Output: enhanced report (string), or original + error message if failed
    """
    if not has_dotenv:
        return basic_report + "\n\nNote: Please install python-dotenv and set GEMINI_API_KEY to use AI."

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return basic_report + "\n\nError: Missing GEMINI_API_KEY in .env file."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""You are a professional software engineer. Rewrite the following daily standup report to be:
- Clear, concise, and well-structured
- Professional tone suitable for team communication
- Keep all original information but improve wording and flow

Original report:
{basic_report}
"""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return basic_report + f"\n\nAI Enhancement Error: {str(e)}"


def main():
    """
    Main function: orchestrate the entire standup report generation process.
    """
    print("Fetching commits from Git...")
    commits = get_commits_from_yesterday()

    print("Generating basic standup report...")
    basic_report = generate_basic_standup_report(commits)

    enhanced_report = basic_report  # Default: no AI enhancement

    # Ask user if they want AI enhancement (only if dependencies are available)
    if has_gemini and has_dotenv:
        user_input = input("\nWould you like to enhance this report with AI? (y/n): ").strip().lower()
        if user_input == 'y':
            print("Enhancing report with Google Gemini AI...")
            enhanced_report = enhance_report_with_ai(basic_report)
        else:
            print("Skipping AI enhancement.")

    # Display final report
    print("\n" + "="*60)
    print(enhanced_report)
    print("="*60)

    # Save reports to files
    with open("demo_output.txt", "w", encoding="utf-8") as f:
        f.write(basic_report)
    print("\nBasic report saved to: demo_output.txt")

    if enhanced_report != basic_report:
        with open("demo_output_ai.txt", "w", encoding="utf-8") as f:
            f.write(enhanced_report)
        print("AI-enhanced report saved to: demo_output_ai.txt")


if __name__ == "__main__":
    main()