from qsystem0_asm2 import ASM_Program
from tqdm import tqdm_notebook as tqdm
import numpy as np
import time

class AveragerProgram(ASM_Program):
    def __init__(self, cfg):
        ASM_Program.__init__(self)
        self.cfg=cfg
        self.make_program()
    
    def initialize(self):
        pass
    
    def initialize_round(self):
        pass
    
    def body(self):
        pass
    
    def update(self):
        pass
    
    def make_program(self):
        p=self
        
        rcount=12
        rii=13
        rjj=14
        rkk=15

        p.initialize()

        p.regwi(0, rcount,0)
        p.regwi (0, rkk, self.cfg["rounds"]-1 )
        p.label("LOOP_K")

        p.initialize_round()
        
        p.regwi (0, rii, self.cfg["expts"]-1 )
        p.label("LOOP_I")    

        p.regwi (0, rjj, self.cfg["reps"]-1)
        p.label("LOOP_J")

        p.body()

        p.mathi(0,rcount,rcount,"+",1)
        
        p.memwi(0,rcount,1)
                
        p.loopnz(0, rjj, 'LOOP_J')

        p.update()
        
        p.loopnz(0, rii, "LOOP_I")    
        p.seti_trigger(t=0)

        p.loopnz(0,rkk, "LOOP_K")

        p.end()        

    def get_n (self, round_num, expt_num, rep_num):
        return (round_num)*self.cfg['expts']*self.cfg['reps'] + (expt_num)*self.cfg['reps']+rep_num

    def get_expt_num (self, n):
        return (n // self.cfg['reps']) % self.cfg['expts']
    
    def get_expt_pts(self):
        return self.cfg["start"]+np.arange(self.cfg['expts'])*self.cfg["step"]
        
    def acquire(self, soc, progress=True):

        self.load_pulses(soc)
        # Readout configuration to route input without frequency translation.
        soc.readout.set_out(sel="product")
        
        # Configure buffer capture.
        soc.avg_buf.config_buf(address=0,length=self.cfg['readout_length'])
        soc.avg_buf.config_avg(address=0,length=self.cfg['readout_length'])

        # Enable buffer capture.
        soc.avg_buf.enable_buf()
        soc.avg_buf.enable_avg()
        soc.tproc.load_asm_program(self)
        
        reps,rounds,expts = self.cfg['reps'], self.cfg['rounds'], self.cfg['expts']
        
        count=0
        last_count=0
        total_count=reps*rounds*expts

        di_buf=np.zeros(total_count)
        dq_buf=np.zeros(total_count)
        
        soc.tproc.stop()
        
        soc.tproc.single_write(addr= 1,data=0)
        self.stats=[]
        with tqdm(total=total_count, disable=not progress) as pbar:
            soc.tproc.start()
            last_nn=0
            while count<total_count-1:
                nn = soc.tproc.single_read(addr= 1)
                if nn<last_nn:
                    wrap=1
                else:
                    wrap=0
                count=(count//2**16+wrap)*2**16 + nn
                last_nn=nn
                if count>=min(last_count+1000,total_count-1):
                    addr=last_count % soc.avg_buf.AVG_MAX_LENGTH
                    length = count-last_count
                    length -= length%2
                    di,dq = soc.get_accumulated(address=addr, length=length)

                    di_buf[last_count:last_count+length]=di[:length]
                    dq_buf[last_count:last_count+length]=dq[:length]

                    last_count+=length
                    self.stats.append( (time.time(), count,addr, length))
                    pbar.update(last_count-pbar.n)
                    #print (count,addr, length)
                    
        self.di_buf=di_buf
        self.dq_buf=dq_buf
        
        avg_di=np.sum(di_buf.reshape((rounds,expts, reps)),(2,0))/(reps*rounds)/self.cfg['readout_length']
        avg_dq=np.sum(dq_buf.reshape((rounds,expts, reps)),(2,0))/(reps*rounds)/self.cfg['readout_length']
        expt_pts=self.get_expt_pts()
        amp_pts=np.sqrt(avg_di**2+avg_dq**2)
        
        return expt_pts, avg_di, avg_dq, amp_pts