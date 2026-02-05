Feature: Timer Functionality
  As a developer
  I want to measure execution time of code blocks
  So that I can track performance of my application

  Background:
    Given a new timer instance

  Scenario: Basic timer start and stop
    When I start the timer
    And I wait for 0.1 seconds
    And I stop the timer
    Then the elapsed time should be approximately 0.1 seconds

  Scenario: Multiple timer measurements
    When I start the timer
    And I wait for 0.05 seconds
    And I stop the timer
    And I start the timer again
    And I wait for 0.05 seconds
    And I stop the timer
    Then the timer should have 2 measurements

  Scenario: Timer reset functionality
    When I start the timer
    And I wait for 0.1 seconds
    And I stop the timer
    And I reset the timer
    Then the timer measurements should be empty

  Scenario: Context manager usage
    When I use the timer as a context manager for 0.1 seconds
    Then the elapsed time should be approximately 0.1 seconds

  Scenario: Getting timer statistics
    When I start the timer
    And I wait for 0.05 seconds
    And I stop the timer
    And I start the timer again
    And I wait for 0.1 seconds
    And I stop the timer
    Then the timer should provide mean time statistics
    And the mean time should be greater than 0
