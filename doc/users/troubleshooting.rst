.. _troubleshooting:

===============
Troubleshooting
===============
- Whenever there are problems when working with the camera
   First make sure you can ping the Timepix camera to ensure a working connection.

   Next try starting the SoPhy software and see if it can communicate properly with the camera.
   Remember to close SoPhy afterwards, as there can only be one process using the address.


- Make sure to load the correct config file.
   If the parameters are off, you might not be able to see anything.


- Use a flashlight!
   When the camera is properly connected and set up, you may use a flashlight
   to shine directly into the lens and next to it in quick succession.


- You can see ToA but no ToF data
    Check and maybe reconfigure the trigger.


- Error: Address is already in use
   If you get this error, look for any other process that is running and uses the corresponding IP and port.
   Also try restarting the camera
