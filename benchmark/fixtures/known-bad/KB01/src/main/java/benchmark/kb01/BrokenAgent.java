package benchmark.kb01;

import com.embabel.agent.api.annotation.AchievesGoal;
import com.embabel.agent.api.annotation.Action;
import com.embabel.agent.api.annotation.Agent;
import com.embabel.agent.api.common.PlannerType;

@Agent(description = "KB01 broken credit flow", planner = PlannerType.GOAP)
public class BrokenAgent {

    @Action(description = "Collect customer profile")
    public Customer collectCustomer(String customerId) {
        return new Customer(customerId, "example");
    }

    @AchievesGoal(description = "Produce a loan decision")
    @Action(description = "Decide on a loan")
    public LoanDecision decideLoan(CreditAssessment assessment) {
        return new LoanDecision(assessment.customerId(), assessment.score() >= 700);
    }
}