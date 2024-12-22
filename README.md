# tacitus
Infrastructure simulation and change verification

## What is it?

Tacitus is (will be) a tool to allow you to simulate and visualize the impact of infrastructure changes before you apply them

The idea is that you will give it a Terraform state file at which it will import all the running cloud infrastructure

You then define data flows through your program, e.g. if I call `/x` it reaches out to another service at `/y` and so on

Finally you give it a Terraform plan outout and it will model those infrastructure changes, apply them to the loaded configuration, and then simulate data flowing through the system to find any access or network issues before the infrastructure is deployed