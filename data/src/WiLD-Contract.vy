#################
###  structs  ###
#################

# Workflow Activity == middle node or leaf
struct Activity:
    identifier: string[32]  # key of activity_registry
        # Note: use the URI fragment as identifier (or its string[32] hash)
    activity_type: uint256
        #    1: AtomicActivity, 2: ConditionalActivity, 3: ParallelActivity, 4: SequentialActivity
    child_activity_index: map(uint256, string[32]) #  map(counter, activity id) | string[32][2] alternativ fixed array implementation, parsing ~ balance tree
        # 
    child_activity_count: uint256 
        # if 0: this == atomic == leaf
    #  pre & post conditions are only needed if you do impicit state flips


# Workflow Model == Tree by id-Reference
struct Workflow:
    identifier: string[32] # key of model_registry
        # Note: use the URI (or its string[32] hash)
    root_activity: string[32]
        #
    
    # owner: address # for parsing protection ?
    
# Instance
struct Instance:
    global_id: uint256
    workflow_ref: string[32]
    # workflow_state: uint256 # not needed, just look at root activity
    activity_states: map(string[32], uint256) # map(Activity Id, state) # workflow is done, if root of workflow is done
        #    0: uninitialised, 1: initialised, 2: initialisedFromListItemOne, 3: active, 4: paused, 5: skipped, 6: doneFromListItemOne, 7: done
    # evtl noch ein (alternatives mapping, "active activities" ?



#################
###   event   ###
#################

Instantiation: event({_workflow_ref: indexed(bytes32), _instance_ref: uint256 })
State_Change: event({_instance_ref: indexed(uint256), _activity_ref: indexed(bytes32), _state: uint256})
    # maybe index the state?

#################
###   props   ###
#################

# Activities
activity_index: public(map(string[32], Activity))

# Workflows
workflow_index: public(map(string[32], Workflow))
# map(workflow identifier, corresponding workflow model)

# Instances
instance_index: public(map(uint256, Instance))
instance_count: public(uint256)

# pre & post conditions mapping ? not needed if explicitlyFlipState

# Instances track their states on their own.
# If something changes in a worklow, you do not need to submit the whole workflow, only upstream tasks!



#################
### functions ###
#################

# Parsing Models
# struct Quad:
#     subj: string[32]   # activity / workflow
#     pred: string[32]   # property
#     obj: string[32]    # value
#     graph: string[32]  # workflow

@public
def parseWorkflow(quad_subject: string[32], quad_predicate: string[32], quad_object: string[32]) -> bool:
    if self.activity_index[quad_subject].identifier == quad_subject:
        raise "### Workflow | Already registered as Activity."

    if self.workflow_index[quad_subject].identifier == '':
        # DO INFERENCE # 
        self.workflow_index[quad_subject].identifier = quad_subject

    # check if type was actually stated
    if quad_predicate == 'rdf:type' and quad_object == 'wild:WorkflowModel' :
        return True # an alternative would be to check if not stated and reject, but thats not really OWA and semantics
    
    # ROOT ACTIVITY
    if quad_predicate == 'wild:hasBehaviour':
        # add new root activity reference to workflow
        self.workflow_index[quad_subject].root_activity = quad_object
        return True

    raise "### Workflow | Can you WiLD ontology please?"



@public
def parseActivity(quad_subject: string[32], quad_predicate: string[32], quad_object: string[32]) -> bool:
    if self.workflow_index[quad_subject].identifier == quad_subject:
        raise "### Activity | Already registred as Workflow."

    if self.activity_index[quad_subject].identifier == '':
        # DO INFERENCE #
        self.activity_index[quad_subject].identifier = quad_subject
    
    if quad_predicate == 'rdf:type':
        #    1: AtomicActivity, 2: ConditionalActivity, 3: ParallelActivity, 4: SequentialActivity
        if quad_object == 'wild:AtomicActivity':
            self.activity_index[quad_subject].activity_type = 1
            return True
        if quad_object == 'wild:ConditionalActivity':
            self.activity_index[quad_subject].activity_type = 2
            return True
        if quad_object == 'wild:ParallelActivity':
            self.activity_index[quad_subject].activity_type = 3
            return True
        if quad_object == 'wild:SequentialActivity':
            self.activity_index[quad_subject].activity_type = 4
            return True

    if quad_predicate == 'wild:hasChildActivity':
        self.activity_index[quad_subject].child_activity_count += 1 # to not start at default 0 but default 1 as id
        child_count: uint256 = self.activity_index[quad_subject].child_activity_count
        self.activity_index[quad_subject].child_activity_index[child_count] = quad_object
        return True
    
    raise "### Activity | Can you WiLD ontology please?"



# Initialising Instances
@public
def initialise(workflow_reference: string[32]) -> uint256:
    if self.workflow_index[workflow_reference].identifier == '':
        raise "### Initialise | Unknown Workflow Reference"
    self.instance_count += 1 # to not start at default 0 but default 1 as id
    self.instance_index[self.instance_count].global_id = self.instance_count
    self.instance_index[self.instance_count].workflow_ref = workflow_reference
    # self.instance_index[self.instance_count].workflow_state = 1 # not needed, just look at root activity
    root_ref: string[32] = self.workflow_index[workflow_reference].root_activity
    self.instance_index[self.instance_count].activity_states[root_ref] = 1
    log.Instantiation(keccak256(workflow_reference), self.instance_count)
    return self.instance_count
    


# Flipping states # explicitlyFlipState
@public
def flipState(instance_ref: uint256, activity_ref: string[32], state: uint256):
    if self.activity_index[activity_ref].identifier == '':
        raise "### State | Unknown Activity Reference"
    if self.instance_index[instance_ref].global_id == 0:
        raise "### State | Unkown Instance Reference"
    # if self.instance_index[instance_ref].activity_states[activity_ref] == 0:
    #     raise "### State | Activity Instance not initialised"
    self.instance_index[instance_ref].activity_states[activity_ref] = state
    log.State_Change(instance_ref, keccak256(activity_ref), state)


# Denk dran 
    # string[32] auf bytes32 und die assert strings umzuwandeln
    # keccak wieder rausnehmen dann ;-)

# Compile
    # vyper -f abi,bytecode ./WiLD-Contract.vy
