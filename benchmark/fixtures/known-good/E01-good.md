# E01 known-good answer (hand-written)

```java src/main/java/benchmark/e01/Greeting.java
package benchmark.e01;

public record Greeting(String message) {}
```

```java src/main/java/benchmark/e01/GreetingActions.java
package benchmark.e01;

import com.embabel.agent.api.annotation.Action;
import com.embabel.agent.api.annotation.EmbabelComponent;

@EmbabelComponent
public class GreetingActions {

    @Action(description = "Greet by name")
    public Greeting greet(String name) {
        return new Greeting("Hello, " + name);
    }
}
```