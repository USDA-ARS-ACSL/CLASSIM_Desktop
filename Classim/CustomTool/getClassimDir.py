import os
import winreg as wrg

def getClassimDir():
    from CustomTool.UI import messageUserInfo
    # Check where classim is installed
    # Store location of HKEY_CURRENT_USER
    location = wrg.HKEY_CURRENT_USER
    # Find path for documents
    keyPath = wrg.OpenKeyEx(location,r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders',0,wrg.KEY_READ)
    
 
    # Query keyPath
    dirPath, reg = wrg.QueryValueEx(keyPath,r'Personal')
    if "%" in dirPath:
        envPathKey = dirPath.split('\\')
        envPathKey1 = os.getenv(envPathKey[0].replace('%',''))
        envPathKey2 = envPathKey[1:][0]
        classimDir = os.path.join(os.path.join(envPathKey1,envPathKey2), 'classim')
    else:
        classimDir = os.path.join(dirPath, 'classim')

    if not os.path.exists(classimDir):
        messageUserInfo(classimDir+' folder with databases and programs is missing.  Please check your setup or ontact the developers at ars-classim-help@usda.gov.')
    return classimDir
