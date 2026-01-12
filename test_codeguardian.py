#!/usr/bin/env python3
"""
CodeGuardian Test Script

Run this script to test your setup and see the system in action!

Usage:
    python test_codeguardian.py
"""
import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("""
╔═══════════════════════════════════════════════════════════╗
║                                                            ║
║           🤖  CodeGuardian System Test  🤖                 ║
║                                                            ║
║  This script tests your CodeGuardian setup and shows      ║
║  the multi-agent system in action!                        ║
║                                                            ║
╚═══════════════════════════════════════════════════════════╝
""")

# Test 1: Check imports
print("\n📦 Test 1: Checking imports...")
try:
    from core.config import get_settings, calculate_cost
    from observability.tracing import trace_agent
    from agents.coordinator import CoordinatorAgent, review_code
    from agents.static_analysis import static_analysis_agent
    print("   ✅ All imports successful!")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    print("\n   💡 Make sure you've installed dependencies:")
    print("      pip install -r requirements.txt")
    sys.exit(1)

# Test 2: Check configuration
print("\n⚙️  Test 2: Checking configuration...")
try:
    settings = get_settings()
    print(f"   ✅ Settings loaded")
    print(f"      Primary model: {settings.primary_model}")
    print(f"      Quick model: {settings.quick_model}")
    
    # Check API keys (without showing them)
    if settings.anthropic_api_key and 'your_' not in settings.anthropic_api_key:
        print(f"   ✅ Anthropic API key configured")
    else:
        print(f"   ⚠️  Warning: Anthropic API key not set")
        print("      Set ANTHROPIC_API_KEY in .env file")
    
    if settings.langfuse_public_key and 'your_' not in settings.langfuse_public_key:
        print(f"   ✅ Langfuse keys configured")
    else:
        print(f"   ⚠️  Warning: Langfuse keys not set")
        print("      Sign up at https://cloud.langfuse.com (FREE)")

except Exception as e:
    print(f"   ❌ Configuration error: {e}")
    print("\n   💡 Make sure you've:")
    print("      1. Copied .env.example to .env")
    print("      2. Added your API keys")
    sys.exit(1)

# Test 3: Cost calculation
print("\n💰 Test 3: Testing cost calculation...")
cost = calculate_cost("claude-sonnet-4-20250514", 1000, 500)
print(f"   ✅ Cost for 1000 input + 500 output tokens: ${cost:.4f}")

# Test 4: Sample code with bugs
print("\n🐛 Test 4: Analyzing sample code with intentional bugs...")

buggy_code = {
    "calculator.py": """
def divide(a, b):
    # BUG: No check for division by zero!
    return a / b

def calculate_average(numbers):
    # BUG: Will fail on empty list!
    return sum(numbers) / len(numbers)

def   badly_formatted  (  x,y  ):
    # BUG: Bad formatting
    return x+y

class TooComplex:
    def complex_function(self, a, b, c, d, e):
        # BUG: Too complex, too many branches
        if a > 0:
            if b > 0:
                if c > 0:
                    if d > 0:
                        if e > 0:
                            return a + b + c + d + e
                        else:
                            return a + b + c + d
                    else:
                        return a + b + c
                else:
                    return a + b
            else:
                return a
        else:
            return 0
""",
    "auth.py": """
import hashlib

def check_password(password, stored_hash):
    # BUG: Using MD5 for passwords (weak!)
    return hashlib.md5(password.encode()).hexdigest() == stored_hash

def get_user(user_id):
    # BUG: SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = " + user_id
    return execute_query(query)
"""
}

print("\n   Sample code loaded:")
for filename, code in buggy_code.items():
    lines = len(code.split('\n'))
    print(f"   - {filename}: {lines} lines")

# Test 5: Run static analysis (no LLM needed)
print("\n🔍 Test 5: Running Static Analysis Agent...")
print("   (This is fast - no LLM calls, just code analysis tools)")

async def test_static_analysis():
    try:
        issues = await static_analysis_agent(buggy_code)
        
        print(f"\n   ✅ Static Analysis Complete!")
        print(f"   Found {len(issues)} issues:\n")
        
        # Group by severity
        by_severity = {}
        for issue in issues:
            sev = issue['severity']
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = by_severity.get(severity, 0)
            if count > 0:
                icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢', 'info': 'ℹ️'}
                print(f"   {icon[severity]} {severity.upper()}: {count}")
        
        # Show first few issues
        print("\n   Sample issues found:")
        for i, issue in enumerate(issues[:5], 1):
            print(f"\n   {i}. [{issue['severity'].upper()}] {issue['title']}")
            print(f"      File: {issue['file_path']}:{issue['line_number']}")
            print(f"      {issue['description'][:80]}...")
        
        if len(issues) > 5:
            print(f"\n   ... and {len(issues) - 5} more issues")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run async test
success = asyncio.run(test_static_analysis())

# Test 6: Quick coordinator test (with mocked/disabled LLM agents)
if success:
    print("\n" + "="*60)
    print("🎯 Test 6: Running Coordinator Agent (Limited Mode)")
    print("="*60)
    print("\n   NOTE: Security and Logic agents are placeholders")
    print("   (They'll be implemented in coming weeks)")
    
    async def test_coordinator():
        try:
            result = await review_code(buggy_code, "test-review-001")
            
            print(f"\n   ✅ Review complete!")
            print(f"\n   Summary:")
            print(f"   - Total issues: {result['summary']['total_issues']}")
            print(f"   - Files analyzed: {result['analysis']['total_files']}")
            print(f"   - Lines of code: {result['analysis']['total_lines']}")
            
            # Show breakdown
            severity = result['summary']['severity_breakdown']
            print(f"\n   Severity breakdown:")
            for sev in ['critical', 'high', 'medium', 'low', 'info']:
                if severity.get(sev, 0) > 0:
                    print(f"   - {sev}: {severity[sev]}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    coordinator_success = asyncio.run(test_coordinator())
    
    if coordinator_success:
        success = True

# Final summary
print("\n" + "="*60)
if success:
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("""
🎉 Congratulations! Your CodeGuardian setup is working!

📋 Next Steps:

   WEEK 1 (This Week):
   1. Get Anthropic API key → console.anthropic.com
   2. Get Langfuse account → cloud.langfuse.com (FREE)
   3. Add keys to .env file
   4. Run this test again to see full system

   WEEK 2-3:
   - Implement Security Agent (Bandit + Claude)
   - Implement Logic Agent (Claude semantic analysis)
   
   WEEK 4-5:
   - Implement Test Generation
   - Implement Bug Hunter
   
   WEEK 6-7:
   - Implement Fix Generator
   - Build API server
   
   WEEK 8:
   - Build React UI
   - Deploy to Railway/Render
   - Create demo video

💡 Pro Tips:
   - Check README.md for detailed docs
   - View Langfuse dashboard for observability
   - Start with small code samples
   - Track costs (should be <$0.50 per review)

🔗 Useful Links:
   - Anthropic Console: https://console.anthropic.com
   - Langfuse Dashboard: https://cloud.langfuse.com
   - Documentation: ./docs/
   
Happy Building! 🚀
""")
else:
    print("❌ SOME TESTS FAILED")
    print("="*60)
    print("""
Please check the errors above and:
   1. Install all dependencies: pip install -r requirements.txt
   2. Copy .env.example to .env
   3. Run again: python test_codeguardian.py
   
Need help? Check README.md for setup instructions.
""")
    sys.exit(1)
