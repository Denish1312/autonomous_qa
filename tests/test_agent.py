import pytest
import asyncio
from src.agent.base import MockAgent

@pytest.mark.asyncio
async def test_mock_agent():
    # Initialize agent
    agent = MockAgent(config={})
    
    try:
        # Test planning
        plan = await agent.plan("https://example.com", "e2e")
        assert len(plan.steps) > 0, "Plan should contain steps"
        print("✅ Plan generation successful")
        
        # Test execution
        result = await agent.execute(plan)
        assert result.success, "Test execution should succeed"
        print("✅ Test execution successful")
        
        # Test analysis
        analysis = await agent.analyze(result)
        assert "summary" in analysis, "Analysis should contain summary"
        print("✅ Result analysis successful")
        
        print("✅ All agent tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing agent: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_mock_agent())
