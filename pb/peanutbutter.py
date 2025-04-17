import pandas as pd

def incAP(ap:int):
    year = int(str(ap)[0:4])
    month = int(str(ap)[4:6])
    if month not in [1,2,3,4,5,6,7,8,9,10,11,12]:
        raise ValueError("Invalid month")
    if month < 12:
        newmonth = month + 1
        newyear = year
    else:
        newmonth = 1
        newyear = year + 1
    return int(str(newyear) + str(newmonth).zfill(2))


class Package:
    def __init__(self, name:str,duration:int,start:int):
        """
        name: str
            The name of the package
        duration: int
            The duration of the package in 
        start: int
            The start date of the package in YYYYMM format
        """
        self.name = name
        self.duration = duration
        self.start = start
        self.load = pd.Series()

    def add_resource(self, name:str, hours:float) -> None:
        self.load.loc[name] = hours
    
    def spread(self) -> pd.DataFrame:
        aps = [self.start]
        startap = self.start
        for _ in range(self.duration-1):
            aps.append(incAP(startap))
            startap = aps[-1]
        newdf = pd.DataFrame(columns = aps,index = self.load.index.to_list())
        for resource in newdf.index:
            newdf.loc[resource,:] = self.load[resource] / self.duration
        return  newdf
    
    def add_aps_constant_work(self,aps:int):
        


    