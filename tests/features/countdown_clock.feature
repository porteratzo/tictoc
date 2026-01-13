Feature: Countdown Clock Functionality
  As a developer
  I want to measure remaining time until a deadline
  So that I can implement time-limited operations

  Scenario: Create countdown clock with duration
    Given a countdown clock with 1.0 seconds duration
    When I check the remaining time immediately
    Then the remaining time should be approximately 1.0 seconds

  Scenario: Countdown clock time progression
    Given a countdown clock with 0.5 seconds duration
    When I wait for 0.2 seconds
    And I check the remaining time
    Then the remaining time should be approximately 0.3 seconds

  Scenario: Countdown clock expiry
    Given a countdown clock with 0.1 seconds duration
    When I wait for 0.15 seconds
    Then the countdown clock should be expired

  Scenario: Reset countdown clock
    Given a countdown clock with 0.5 seconds duration
    When I wait for 0.2 seconds
    And I reset the countdown clock
    And I check the remaining time
    Then the remaining time should be approximately 0.5 seconds
