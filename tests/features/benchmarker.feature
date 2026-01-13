Feature: Benchmarker Functionality
  As a developer
  I want to benchmark different code execution steps
  So that I can identify performance bottlenecks

  Background:
    Given a new benchmarker instance

  Scenario: Basic step timing
    When I start timing a step called "initialization"
    And I wait for 0.05 seconds
    And I stop timing the step "initialization"
    Then the benchmarker should have recorded the step "initialization"
    And the step "initialization" time should be approximately 0.05 seconds

  Scenario: Multiple steps benchmarking
    When I start timing a step called "step1"
    And I wait for 0.03 seconds
    And I stop timing the step "step1"
    And I start timing a step called "step2"
    And I wait for 0.05 seconds
    And I stop timing the step "step2"
    Then the benchmarker should have 2 recorded steps
    And the step "step1" should exist
    And the step "step2" should exist

  Scenario: Repeated step measurements
    When I measure step "processing" 3 times with 0.02 second delays
    Then the step "processing" should have 3 measurements
    And the mean time for "processing" should be approximately 0.02 seconds

  Scenario: Context manager for steps
    When I use benchmarker context manager for step "context_step" with 0.05 second delay
    Then the benchmarker should have recorded the step "context_step"
    And the step "context_step" time should be approximately 0.05 seconds

  Scenario: Getting benchmarker results
    When I start timing a step called "task1"
    And I wait for 0.03 seconds
    And I stop timing the step "task1"
    And I start timing a step called "task2"
    And I wait for 0.04 seconds
    And I stop timing the step "task2"
    Then I should be able to get benchmark results
    And the results should contain step "task1"
    And the results should contain step "task2"
