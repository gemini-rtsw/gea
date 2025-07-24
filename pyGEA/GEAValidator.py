#!/usr/bin/python

import GEAVars

class BaseValidator(object):

    def __init__(self):
        """Each type of validator should overwrite this class.
        """
        raise NotImplemented("__init__() not implemented.\n")
        
    def _handleError(self, errorText, stream, valueOnError, errorPreText=None):
        """If stream or velueOnError is None, raise an exception.
        Otherwise, write error to the stream, and return valueOnError.
        """
        errorPreText=errorPreText or ''
        
        #MIGHT CHANGE... 
        if stream is None or valueOnError is None:
            raise ValueError(errorText)
        else:
            #Show something when dealing with an empty string.
            if valueOnError=='':
                strValueOnError="''"
            else:
                strValueOnError=valueOnError
                
            stream.write(errorPreText+errorText)
            stream.write('\nSetting default value: %s\n' % strValueOnError)
            return valueOnError
            
    def validate(self, value):
        
        raise NotImplemented("validate() not implemented.\n")
        
class BooleanValidator(BaseValidator):

    trueChoices=['on', 'On', 'ON', 'true', 'True', 'TRUE', 
                 'checked', 'yes', 'Yes', '1', True, 1]
    falseChoices=['off', 'Off', 'OFF', 'false', 'False', 'FALSE', 
                 'no', 'No', '0', False, 0]

    def __init__(self, choiceTrue=True, choiceFalse=False, 
                stream=GEAVars.errStream, valueOnError=None, errorPreText=None):
        """
        Arguments:
        ...
        stream - If provided, error text which is passed to an Exception object is also written here.
        valueOnError - If provided, when an exception during conversion is raised and stream is defined, 
        this value is returened. The error is written to the stream. 
        """
        self.choiceTrue=choiceTrue
        self.choiceFalse=choiceFalse
        self.stream=stream
        self.valueOnError=valueOnError
        self.errorPreText=errorPreText
        
    def validate(self, option):
        
        if option in BooleanValidator.trueChoices:
            return self.choiceTrue
        elif option in BooleanValidator.falseChoices:
            return self.choiceFalse
        else:
            return BaseValidator._handleError(self, "Could not convert '%s' to boolean" % option, 
                                          self.stream, self.valueOnError, self.errorPreText)    
                                          
class IntValidator(BaseValidator):

    def __init__(self, minVal=None, maxVal=None, 
                stream=GEAVars.errStream, valueOnError=None, errorPreText=None):
        """
        Arguments:
        ...
        stream - If provided, error text which is passed to an Exception object is also written here.
        valueOnError - If provided, when an exception during conversion is raised and stream is defined, 
        this value is returened. The error is written to the stream. 
        """
        self.minVal=minVal
        self.maxVal=maxVal
        self.stream=stream
        self.valueOnError=valueOnError
        self.errorPreText=errorPreText
        
    def validate(self, option):
    
        try: 
            val=int(option)
        except ValueError:
            return BaseValidator._handleError(self, "Could not convert '%s' to int" % option, 
                                       self.stream, self.valueOnError, self.errorPreText)   

        if self.minVal is not None:
            if self.minVal>val:
                return BaseValidator._handleError(self, 'Value %d is smaller than minimum %d' % (val, self.minVal), 
                                       self.stream, self.valueOnError, self.errorPreText)   

        if self.maxVal is not None:
            if self.maxVal<val:
                return BaseValidator._handleError(self, 'Value %d is larger than maximum %d' % (val, self.maxVal), 
                                       self.stream, self.valueOnError, self.errorPreText)   
        return val
   
class FloatValidator(BaseValidator):

    def __init__(self, minVal=None, maxVal=None, 
                stream=GEAVars.errStream, valueOnError=None, errorPreText=None):
        """
        Arguments:
        ...
        stream - If provided, error text which is passed to an Exception object is also written here.
        valueOnError - If provided, when an exception during conversion is raised and stream is defined, 
        this value is returened. The error is written to the stream. 
        """
        self.minVal=minVal
        self.maxVal=maxVal
        self.stream=stream
        self.valueOnError=valueOnError
        self.errorPreText=errorPreText
        
    def validate(self, option):
        
        try: 
            val=float(option)
        except ValueError:
            return BaseValidator._handleError(self, "Could not convert '%s' to int" % option, 
                                       self.stream, self.valueOnError, self.errorPreText)   

        if self.minVal is not None:
            if self.minVal>val:
                return BaseValidator._handleError(self, 'Value %f is smaller than minimum %f' % (val, self.minVal), 
                                       self.stream, self.valueOnError, self.errorPreText)   

        if self.maxVal is not None:
            if self.maxVal<val:
                return BaseValidator._handleError(self, 'Value %f is larger than maximum %f' % (val, self.maxVal), 
                                       self.stream, self.valueOnError, self.errorPreText)   
        return val
        

if __name__=='__main__':
  
    vBool=BooleanValidator(valueOnError='True',
                           errorPreText='Validating %s... ' % 'balsdf')
    
    yo=vBool.validate('On')
    print yo
    
    vInt=IntValidator(valueOnError='34', minVal=22, maxVal=344,
                           errorPreText='Validating %s... ' % 'balsdf')
                           
    yo2=vInt.validate('-23')
    print yo2
    
    vFloat=FloatValidator(valueOnError='345454', minVal=22, maxVal=344,
                           errorPreText='Validating %s... ' % 'balsdf')
                           
    yo3=vFloat.validate('344.3342343')
    print yo3
