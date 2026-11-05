"""One dispatch-process derivation; current-byte checks continue across side effects.
Never persist this context. Independent receipt/complete still perform full validation.
"""
import copy,sys
import registration_validation as rv
import verification_session as vs

def business_state(s,batch):
    value=copy.deepcopy(s)
    value.pop('events',None);value.pop('updated_at',None)
    value['batches'][batch].pop('send_jobs',None)
    return rv.canonical(value)

def require(ok,message):
    if not ok:raise ValueError(message)

class DispatchContext:
    def __init__(self,workflow,s,batch,orders,session):
        self.workflow=workflow;self.state=s;self.batch=batch
        self.baseline=business_state(s,batch);self.fixed=copy.deepcopy(orders)
        self.by_part={o['part']:o for o in self.fixed}
        require(len(self.by_part)==len(self.fixed),'dispatch-context-duplicate-parts')
    def orders(self):return copy.deepcopy(self.fixed)
    def check(self,s,batch,order=None):
        require(s is self.state and batch==self.batch,'dispatch-context-owner-conflict')
        require(business_state(s,batch)==self.baseline,'dispatch-context-business-state-changed')
        # Full transitive dependencies and canonical live prefix guards: no passed flag.
        for part,entry in s['batches'][batch]['send_jobs'].items():
            require(part in self.by_part and entry['order']==self.by_part[part],'dispatch-context-order-changed')
        if order is not None:require(order==self.by_part.get(order.get('part')),'dispatch-context-order-changed')
    def checked_orders(self,s,batch):
        self.check(s,batch);return copy.deepcopy(self.by_part)

def derive(workflow,s,batch):
    import region_frame_capture
    # Imports/decoder initialization happen before this pure scope. No sender/write lives here.
    with rv.pure_scope(region_frame_capture) as session:
        orders=workflow.send_orders(s,batch)
    return DispatchContext(workflow,s,batch,orders,session)
