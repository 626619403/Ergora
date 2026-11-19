# Ergora collaboration domain

Ergora organizes work assignments, decisions, and acceptance in code development and training experiments. The following terms distinguish the work itself, the participants performing it, and the actual tools used.

## Language

**Task**:
A unit of work with explicit goals, scope, and acceptance requirements; one issue may be associated with multiple task revisions.
_Avoid_: Treating a task and an issue as the same object.

**Task Contract**:
The inputs, working agreements, project constraints, and acceptance requirements frozen for a task.

**Role**:
Responsibilities and permissions for a type of work, such as implementer, verifier, or reviewer; a role is independent of the tool performing it.
_Avoid_: Substituting model or tool names for roles.

**Agent**:
An automated participant performing a collaboration role; different participants may perform the same role in different tasks.

**Work Unit**:
A dispatchable piece of a development task with an explicit modification scope, completion requirements, and prerequisite dependencies.
_Avoid_: Using work unit, role, and complete task interchangeably.

**Workflow Package**:
Reusable conventions for stages, role responsibilities, and acceptance materials, shared by a class of tasks.

**Project Policy**:
Work boundaries, required checks, approval requirements, and resource limits set by project maintainers.

**Tool Binding**:
The selection mapping a role to its tool and runtime environment for an execution within a project.

**Acceptance Evidence**:
Reviewable check results and original materials bound to the exact delivery candidate.
_Avoid_: Equating an agent's self-reported completion or runtime logs directly with acceptance passing.

**Human Approval**:
A decision by a person with decision-making authority to authorize an explicit plan or set of evidence materials.
_Avoid_: Equating a model review conclusion with human approval.
