# monitor_5071a
The purpose of this project is to monitor the measurements on a 5071A cesium clock and detect end-of-life (EOL) indicators for the cesium beam tube (CBT). It uses python to read the measurements from the clock and to store these measurements in a sqlite database, and it uses grafana to graph and monitor the data. Upon detecting EOL indicators, Grafana can send an alert by email, Microsoft Teams, or various other means.

<img width="959" alt="image" src="https://github.com/JonahS1/monitor_5071a/assets/51928448/9260ef67-ce7f-4cd5-a610-e9640fadef49">

## How to use it
### Prerequisites
You will need the following in order to use this 5071A monitoring solution:
- a computer/server that can run 24/7
- a serial connection to your 5071A
  - see Chapter 5 of the [5071A User's Guide](https://ww1.microchip.com/downloads/en/DeviceDoc/5071A-Primary-Frequency-Standard-Users-Guide-DS50003249.pdf) (page 44) for more information
  - note that the 5071A is a DTE device which means you will need a serial crossover cable to connect it to your computer/server
- python 3
- Grafana
- dependencies:
  - [sqlite](https://www.sqlite.org/download.html)
  - [pyvisa](https://pyvisa.readthedocs.io/en/latest/introduction/getting.html)
  - [astropy](https://pypi.org/project/astropy/)
  - [pytz](https://pypi.org/project/pytz/)

### Setting up the python
1. Clone this repository.
2. Install all of the dependencies if you don't have them already (they are listed at the end of the [Prerequisites](https://github.com/JonahS1/monitor_5071a/edit/main/README.md#prerequisites) section).
3. In line 8 of `read5071a.py`, set `LOCALTIMEZONE` to your local timezone
4. In line 9 of `update-db.py`, set `RESOURCE` to the resource corresponding to your 5071A. If you do not know what this resource is, you can find it as follows:
    - Run `python3` at the command line.
    - `import pyvisa`
    - `rm = pyvisa.ResourceManager()`
    - `rm.list_resources()` This will list all the available resources, one of which is your 5071A.
    - Pick a resource from the list and run `inst = rm.open_resource('[THE RESOURCE YOU PICKED]')`.
    - `inst.write_termination = '\r\n'`
    - `inst.read_termination = 'scpi >'`
    - `inst.query('*IDN?')` If you picked the correct resource, this should return a string that says `5071A` (along with the manufacturer and some numbers). Otherwise, repeat this process with a different resource until you find it.
    - I think it might always start with `ASRL`, but I am not certain so take this with a grain of salt.
    - If there are a large number of resources, you could try disconnecting the serial connection and seeing which resource disappears when you run `rm.list_resources()` again.
5. Once you find the correct resource and put it into line 9 of `update-db.py`, test that it works by running `update-db.py`. It worked if it made a file in the same directory as the python files called `clock-data-[YOUR CBT SERIAL NUMBER].db`.
    - If you are having trouble getting this to work, you can use the `status5071a.sh` shell script to test the serial connection to your 5071A independent of the python implementation. First, edit the file and set the `DEVICE` variable to your serial device. Next, run the script. It should print all of the data from the 5071A.
6. If you would like to monitor more than one 5071A, do the following steps:
    - Make a duplicate of the `update-db.py` file for each 5071A (make sure to give each file a unique name).
    - Update the `RESOURCE` variable in line 9 of each `update-db.py` file to the corresponding 5071A.
    - Run each `update-db.py` file and verify that a unique `clock-data-[CBT SN].db` file was created for each one.
7. Create a cronjob to update your database(s) on the 30 minute mark of every hour (this is to avoid read/write collisions on the database, since Grafana will read it at the start of every hour).
    - At the command line, run `crontab -e` to edit the crontab file.
    - At the bottom of the file, add the line `30 * * * * cd [ABSOLUTE PATH TO THE DIRECTORY WHERE YOUR PYTHON FILES ARE]; python3 ./update-db.py`.
      - If you have more than one 5071A, you can use this instead: `30 * * * * cd [ABSOLUTE PATH TO DIRECTORY]; python3 ./update-db1.py; python3 ./update-db2.py; [etc]`.
    - Make sure to save the file.

For reference, here is an example of a row in the database:

| **Thermometer** | **"\+5V  supply"** | **"\-12V supply"** | **"\+12V supply"** | **"uP Clock PLL"** | **"87MHz PLL"** | **"DRO Tuning"** | **"SAW Tuning"** | **"Mass spec"** | **"HW Ionizer"** | **"Ion Pump"** | **"Osc\. Oven"** | **"CBT Oven Err"** | **"CBT Oven"** | **"Signal Gain"** | **E\-multiplier** | **"C\-field curr"** | **"Zeeman Freq"** | **"RF amplitude 2"** | **"RF amplitude 1"** | **"Osc\. control"** | **"Freq Offset"** | **"Log status"** | **"Power source"** | **"Status summary"** | **"CBT ID"**    | **EUT\_MJD**     | **EUT\_IDN**               | **NOW\_UNIX**     | **NOW\_MJD**             | **NOW\_LOC**                      | **NOW\_UTC**                      |
|-----------------|--------------------|--------------------|--------------------|--------------------|-----------------|------------------|------------------|-----------------|------------------|----------------|------------------|--------------------|----------------|-------------------|-------------------|---------------------|-------------------|----------------------|----------------------|---------------------|-------------------|------------------|--------------------|----------------------|-----------------|------------------|----------------------------|-------------------|--------------------------|-----------------------------------|-----------------------------------|
| "45\.2 C"       | "5\.4 V"           | "\-12\.3 V"        | "12\.3 V"          | "3\.2 V"           | "1\.8 V"        | "3\.8 V"         | "0\.0 V"         | "11\.9 V"       | "0\.9 V"         | "3\.4 uA"      | "\-9\.0 V"       | "0\.00 C"          | "8\.7 V"       | "14\.4 %"         | "1321 V"          | "12\.117 mA"        | "39949 Hz"        | "22\.3 %"            | "23\.7 %"            | "\-14\.42 %"        | 0e\-15            | Empty            | AC                 | "Operating normally" | US50120909\(H\) | "60137 20:30:04" | "SYMMETRICOM,5071A,0,5216" | 1689193801\.81609 | "MJD 60137\.85418768628" | "Wed Jul 12 04:30:01 PM EDT 2023" | "Wed Jul 12 08:30:01 PM UTC 2023" |

Now that your python files are working and you have created the database file(s), it is time to set up Grafana.

### Setting up Grafana
1. [Install Grafana](https://grafana.com/docs/grafana/latest/setup-grafana/installation/).
2. [Start the Grafana server](https://grafana.com/docs/grafana/latest/setup-grafana/start-restart-grafana/).
3. Open a web browser and go to either `http://localhost:3000/` (if your browser is on the same machine that's running Grafana) or `[YOUR SERVER'S IP ADDRESS]:3000` (if you are accessing Grafana from another machine). Log into Grafana with username: `admin` and password: `admin`, then change the password to something more secure.
4. [Update the Grafana configuration file](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/) to change the following settings:
    - Under the `[server]` section, set `domain` to `[YOUR SERVER'S IP ADDRESS]`. This is not strictly necessary, but it is helpful if you would like to access Grafana from another machine. When Grafana sends you an alert, it will include a link to the dashboard which uses this domain.
    - Under the `[auth.anonymous]` section, set `enabled` to `true` if you would like to allow other people to view the Grafana dashboard without needing to log in.
    - If you have an smtp server and you would like to use it to get email alerts from Grafana, change the settings under the `[smtp]` section. You may not need to change all of these settings to get email to work, depending on the setup of your smtp server.
    - Make sure to uncomment the lines you changed by removing the semicolons before them, and [restart the Grafana server](https://grafana.com/docs/grafana/latest/setup-grafana/start-restart-grafana/) for the changes to take effect.
5. Install the [Grafana sqlite plugin](https://grafana.com/grafana/plugins/frser-sqlite-datasource/?tab=installation), which allows Grafana to use a sqlite database as a data source.
6. Connect Grafana to your database file(s) by adding a sqlite data source:
    - Open Grafana in the web browser and log in as admin if you're not already logged in from step 3.
    - Go to `Menu` (hamburger icon) > `Connections` > `Your connections` > `Data sources`.
    - Click `Add new data source`
    - Search `sqlite`. The plugin should come up. If it does not, make sure you installed it (this was step 5).
    - Click on the SQLite plugin and enter the data source name and the filepath of the `clock-data-[CBT SN].db` file, making sure you use an absolute path. You can leave the other options at their default values.
    - Click `Save & test`. Grafana will tell you whether the database was successfully connected. If it failed, make sure you have entered an absolute path and the file name is spelled correctly.
    - If you would like to monitor more than one 5071A, make sure to set up a data source for each database and give each one a unique name.
7. Create the dashboard by importing `monitor-5071a-dashboard.json` into Grafana.
    - Navigate to `Menu` (hamburger icon) > `Dashboards`.
    - Click `New` > `Import` and upload the json file. Fill out the information on the resulting page, making sure that you don't duplicate the dashboard name or uid.
      - If you are only monitoring one 5071A, you only have to select the sqlite data source you set up in step 6 and then click `Import`.
      - If you are monitoring more than one 5071A, make a dashboard for each clock by re-importing the json file. Make sure to give each dashboard a unique name and uid, and choose the corresponding sqlite data source for each one.
    - After clicking `Import`, you should see the dashboard come up with all the graphs on it.
8. Create contact point(s) and alert rules so that you can get notified when Grafana detects EOL indicators.
    - Navigate to `Menu` (hamburger icon) > `Alerting` > `Contact points`. Click `Add contact point` and set up whichever contact points you want. [Here](https://grafana.com/docs/grafana/latest/alerting/fundamentals/contact-points/) is the documentation on contact points.
    - Navigate to `Menu` > `Alerting` > `Alert rules`. Click `Create alert rule`.
    - Note that if you are monitoring more than one 5071A, you will need to duplicate the alert rules for each of your clocks. Make sure to give them unique names and to set the correct data source for the queries.
    - First we will create the `Electron Multiplier Voltage Threshold` alert rule. This rule will fire if the EMV rises above a certain value.
      - Set the rule name to `Electron Multiplier Voltage Threshold`.
      - Below the rule name, you will see the default query which is named `A`. Change the time range of the query to be from `now-1d` to `now`.
      - Delete the default contents of the query and paste in the following:
        
        ```
        SELECT CAST([NOW_UNIX] AS INT) as time, CAST(TRIM([E-multiplier], 'VCuA% ') AS REAL) as 'Electron Multiplier'
        from data
        WHERE time >= $__from / 1000 and time < $__to / 1000
        ```
      - Click the dropdown menu next to `Format as:` and select `Time series`. The final query should look like this:
        
        ![image](https://github.com/JonahS1/monitor_5071a/assets/51928448/5127668b-2b85-4341-b170-b942dd325969)
      - Set up the B and C expressions to match these settings:
        
        ![image](https://github.com/JonahS1/monitor_5071a/assets/51928448/ebed76d6-ed87-441f-839e-47274fb48bbf)
        - Different 5071As may run with different EMV values. If your 5071A typically runs close to or greater than 1400V, you may want to increase this threshold.
      - Set both the `folder` and the `evaluation group` to `Cesium Clock`. Set the both the `evaluation interval` and the `for` value to `1h`.
      - Set the following annotations:
        - `Alert ID`: `electron-multiplier-voltage-threshold`
        - `Description`: `This will alert if the electron multiplier voltage has risen above 1400V. If the electron multiplier voltage is increasing, this could be an indication that the CBT will fail within the next few weeks.` (make sure to change the threshold if you used a number other than 1400V)
        - `Summary`: `Electron multiplier voltage has risen above 1400V`
      - Create a custom label. Set the key to `project` and the value to `cesium-clock`.
      - Scroll back to the top and click `Save and exit`.
    - Now we will create the `Electron Multiplier Voltage Increase` alert rule, starting with a copy of the rule we just created as a template.
      - From the `Alert rules` page, make a copy of the `Electron Multiplier Voltage Threshold` alert rule. Name the copy `Electron Multiplier Voltage Increase`.
      - Change the name of the query from `A` to `Interval1`.
      - Duplicate the query and change the name of the duplicate to `Interval2`.
      - Change the time range of `Interval1` to be from `now-2d` to `now-1d`.
      - Set up 4 expressions below the queries as follows:
        
        ![image](https://github.com/JonahS1/monitor_5071a/assets/51928448/bf80bf6e-4182-43f5-bc01-540d7b5b3a42)
      - Change the `Alert ID` to `increasing-electron-multiplier-voltage`
      - Change the `Description` to `This will alert when the average electron multiplier voltage (EMV) over the past day is more than 5V greater than the average EMV over the day before that. In other words, it means that the EMV has been increasing over the past 2 days. If the EMV is increasing, the CBT may fail within the next few weeks.`
      - Change the `Summary` to `Electron multiplier voltage is increasing`.
      - Scroll to the top and click `Save and exit`.
    - Create the `RF Amplitude 1 Decrease` alert rule by copying the `Electron Multiplier Voltage Increase` alert rule.
      - Set the name to `RF Amplitude 1 Decrease`.
      - Set both the `Interval1` and `Interval2` queries to the following:
        
        ```
        SELECT CAST([NOW_UNIX] AS INT) as time, CAST(TRIM([RF amplitude 1], 'VCuA% ') AS REAL) as 'RF Amplitude 1'
        from data
        WHERE time >= $__from / 1000 and time < $__to / 1000
        ```
      - In the `Comparison` expression, change the condition to `IS BELOW -0.05`.
      - Set the `Alert ID` to `decreasing-rf-amplitude-1`.
      - Set the `Description` to `This will alert when the average RF amplitude 1 over the past day is more than 0.05% less than the average RF amplitude 1 over the day before that. In other words, it means that the RF amplitude 1 has been decreasing over the past 2 days. If the RF amplitude 1 is decreasing, the CBT may fail within the next few weeks.`
      - Set the `Summary` to `RF amplitude 1 is decreasing`.
      - Scroll to the top and click `Save and exit`.
    - Create the `RF Amplitude 2 Decrease` alert rule by copying the `RF Amplitude 1 Decrease` alert rule.
      - Set the name to `RF Amplitude 2 Decrease`.
      - Set both the `Interval1` and `Interval2` queries to the following:

        ```
        SELECT CAST([NOW_UNIX] AS INT) as time, CAST(TRIM([RF amplitude 2], 'VCuA% ') AS REAL) as 'RF Amplitude 2'
        from data
        WHERE time >= $__from / 1000 and time < $__to / 1000
        ```
      - Set the `Alert ID` to `decreasing-rf-amplitude-2`.
      - Set the `Description` to `This will alert when the average RF amplitude 2 over the past day is more than 0.05% less than the average RF amplitude 2 over the day before that. In other words, it means that the RF amplitude 2 has been decreasing over the past 2 days. If the RF amplitude 2 is decreasing, the CBT may fail within the next few weeks.`
      - Set the `Summary` to `RF amplitude 2 is decreasing`.
      - Scroll to the top and click `Save and exit`.
     
Now that you have set up the dashboard, contact points, and alert rules, you will be notified if Grafana detects any EOL indicators. If you would like to view the data, you can always navigate to the dashboard to see the graphs. You should see the graphs update over time as the cronjob runs the python every hour and adds more data to the database.

## Implementation
- read5071a.py uses pyvisa to get the mesaurements from the clock.
- update-db.py parses the output from read5071a.py, creates a sqlite database if it doesn't exist yet, and adds a new row with the latest clock data.
- A cronjob repeatedly calls update-db.py to continually update the database.
- Grafana uses [sqlite plugin](https://grafana.com/grafana/plugins/frser-sqlite-datasource/) to read the database and display graphs.
  - There are 8 graphs on the dashboard, 6 of which always show the same measurements. These were chosen because they are relevant to EOL prediction or detection. If you hover over the "i", it will explain what that graph has to do with EOL prediction/detection.
  - Dropdown menus at the top control which measurements are displayed on the last 2 graphs.
  - The time range of the graphs can be controlled using a dropdown at the top right corner of the dashboard.
- Grafana monitors data and sends alerts to a Teams channel and specified email addresses if it detects any EOL indicators. Grafana has many possible "contact points," so you don't have to use Teams or email if you would rather be alerted a different way.
- here are the four EOL indicators Grafana is continually looking for:
  1) Electron Multiplier Voltage (EMV) Increasing: This will alert when the average EMV over the past day is more than 5V greater than the average EMV over the day before that. In other words, it means that the EMV has increased over the past 2 days.
  2) Electron Multiplier Voltage Threshold: This will alert if the EMV has risen above 1400V (at the time of writing this, ours is around 1320V). You may want to set a different threshold value depending on where your EMV is currently sitting (this could vary from clock to clock).
  3) RF Amplitude 1 Decreasing: This will alert when the average RF amplitude 1 over the past day is more than 0.05% less than the average RF amplitude 1 over the day before that. In other words, it means that the RF amplitude 1 has decreased over the past 2 days.
  4) RF Amplitude 2 Decreasing: This will alert when the average RF amplitude 2 over the past day is more than 0.05% less than the average RF amplitude 2 over the day before that. In other words, it means that the RF amplitude 2 has decreased over the past 2 days.
- The values for increasing/decreasing checks were chosen based the graphs at the end of [this paper](https://apps.dtic.mil/sti/pdfs/ADA508048.pdf).
  - There are essentially two types of values that make up these checks: the time period over which to take the two averages (= averaging period) and the required difference between the averages for the alert to be triggered (= triggering difference).
  - First, the averaging period was set to two days (one day for each average). Looking at the graphs in the paper, this seemed like a reasonable middle ground. If the averaging period is too small, there may not be enough time for the value to change or you may detect a random fluctuation that is not indicative of a general trend. If the averaging period is too large, it will take longer to pull the average up or down and so the alert will not react to the change as quickly.
  - Next, the triggering difference was found using the ratio of the triggering difference to the averaging period. This ratio is essentially the slope of the graph. The slopes of the graphs in the paper near the area where the value first started increasing or decreasing were used along with the averaging period of 2 days to calculate a reasonable triggering difference.
    - EMV increasing: at the start of the increase, the EMV graph seems to have a slope of about 40V in 4 days, or 10V/day. An averaging period of 2 days actually corresponds to a horizontal change of 1 day, as the average of each day can be thought of as a point at the center of the 24 hours. Therefore, we can multiply the 10V/day slope by 1 day to obtain a triggering difference of 10V. This was then divided by two, as the slope was a rough estimate and it is better to err on the side of caution (a smaller triggering difference will trigger more easily). Thus, the triggering difference used in Grafana was 5V.
    - RF amplitude decreasing: at the start of the decrease, the RF amplitude graphs have a slope of about 0.2% in 2 days, or 0.1%/day. Multiplying by 1 day and dividing by 2 as before gives a triggering difference of 0.05%. This was used for both RF amplitude 1 and RF amplitude 2, as their graphs have fairly similar shapes.
- All the alert rules are evaluated by Grafana once every hour (the cronjob also runs the python script every hour, but it is offset to be on the 30 minute mark of each hour to avoid read/write collisions). If an alert fires, it sends a notification to whichever [contact points](https://grafana.com/docs/grafana/latest/alerting/fundamentals/contact-points/) are set up.
  - Note: if you would like to receive email alerts from Grafana, you must have a working smtp server to configure Grafana with.

## Acknowledgements/References
I would like to thank Jim Sandoz for writing the `status5071a.sh` script and compiling resources to help me get started, as well as continued support during the project. I would also like to acknowledge the authors of all below papers on CBT failure prediction. Without them, this project would not have been possible.

The following resources were very helpful in the creation of this tool:
- https://apps.dtic.mil/sti/pdfs/ADA508048.pdf
- https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8256887
- http://time.kinali.ch/ptti/2002papers/paper10.pdf
