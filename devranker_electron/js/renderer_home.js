try {
  // Logs from Node.js(console.log wont work in renderer.js as this is not associated with main process, but from Html Script Tag)  
  var nodeConsole = require('console');
  var { PythonShell } = require('python-shell');
  var myConsole = new nodeConsole.Console(process.stdout, process.stderr);
  const { ipcRenderer } = require('electron')
  const { remote } = require('electron')
  // To handle Files 
  const fs = require('fs');

  // REST API Upload
  var TAG = '\n(renderer_main.js::)\n'
  let URL = 'http://localhost:5000/predict'
  var pythonFileName = 'py/devranker_functions.py'
  // to replace os.path.join in python
  var path = require('path');

  // To make API Calls, Especially to Upload Anonymized file
  const axios = require('axios');

  let dictDatesForMining = {
    from: "",
    to: ""
  }

  // Required file paths
  let pathInfo = {
    devranker_dir: "",
    output_file_name: "",
    gitDirectory: "",
    DestDirectory: "",
    email_hash_dict_file_path: "",
    anonymized_file_path: "",
    predicted_file_path: "",
    de_anonymized_file_path: "",
  };


  // ***********************************************
  // ***********        FUNCTIONS        ***********
  // ***********************************************
  // Asynchronous - Receiver for Communication
  ipcRenderer.on('asynchronous-reply-setPathInfo', (event, arg) => {
    console.log('renderer_home.js::anynchronous-reply-pathInfo::', arg)
  })

  async function apicall_getPredictionsFile(file_name) {
    const fs = require('fs');
    const got = require('got')
    const FormData = require('form-data');
    var formData = new FormData();
    formData.append('anonymised_file', fs.createReadStream(pathInfo.anonymized_file_path));
    // TODO: Ravi - Replace this code to get file name from Response
    let filePath = path.join(pathInfo.devranker_dir, 'cpu_scores_' + file_name)
    try {
      const res = await got.stream(URL, {
        method: 'POST',
        body: formData,
        headers: {
          ...formData.getHeaders()
        }
      }).pipe(fs.createWriteStream(filePath)).
        on("finish", () => {

          pathInfo.predicted_file_path = filePath
          ann_predictions_file.innerHTML = pathInfo.predicted_file_path

          alert('Predictions File Generated Successfully.\n\nFile Location is:\n' + filePath)
          update_STEP_2_StatusBarColor()
          myConsole.log(`File downloaded to ${filePath}`);
        }).
        on("error", (error) => {
          alert('Predictions Failed, Please try again later.\n\n' + error.message)
          myConsole.error(`Could not write file to system: ${error}`);
        })
    } catch (e) {
      console.log(e);
    }
  }

  function initAndCreateDevRankerDirectoryIfNotExisting() {

    pathInfo.devranker_dir = path.join(pathInfo.DestDirectory, 'Devranker')

    if (!fs.existsSync(pathInfo.devranker_dir)) {
      fs.mkdirSync(pathInfo.devranker_dir);
      alert('Created working Directory: \n\n' + pathInfo.devranker_dir)
    }
  }

  // To check whether Date Radiobutton selected or not
  function isDateRangeSelected() {
    return radio_btn_choice2.checked == true
  }

  function update_STEP_1_StatusBarColor() {
    id_for_step_1_status.className = "status_completed";
  }

  function update_STEP_2_StatusBarColor() {
    id_for_step_2_status.className = "status_completed";
  }

  function update_STEP_3_StatusBarColor() {
    id_for_step_3_status.className = "status_completed";
  }

  function update_STEP_4_StatusBarColor() {
    id_for_step_4_status.className = "status_completed";
  }
  // Asynchronous - Sender
  function storePathInfoInMainJs() {
    ipcRenderer.send('asynchronous-setPathInfo', pathInfo)
    myConsole.log(TAG, 'btn_browse_dest_dir/pathInfo:', pathInfo)
  }

  // ***********************************************
  // ***********      CLICK EVENTS       ***********
  // ***********************************************
  // Clone Repository
  btn_browse_cln_repo.addEventListener('click', async (event) => {

    try {
      const pathArray = await remote.dialog.showOpenDialog({ properties: ['openDirectory'] })

      let pathSel = pathArray.filePaths

      if (pathSel == '') {
        return
      }

      cln_repo.innerHTML = pathSel

      // Communicate with Python
      let options = {
        mode: 'text',
        args: ['check_git_dir', pathSel]
      };

      PythonShell.run(pythonFileName, options, function (err, results) {

        myConsole.log(TAG, 'error:', err, 'resp_result:', results)

        let data_parsed = JSON.parse(results[0])

        if (data_parsed.status == true) {
          pathInfo.gitDirectory = pathSel.toString()
        } else {
          alert(pathSel + '\n\n' + data_parsed.msg)
          cln_repo.innerHTML = ''
        }

        myConsole.log(TAG, 'btn_browse_cln_repo/pathInfo:', pathInfo)

      });
    } catch (err) {
      alert(err)
    }
  });

  // Browse Destination Directory
  btn_browse_dest_dir.addEventListener('click', async (event) => {
    try {
      const pathArray = await remote.dialog.showOpenDialog({ properties: ['openDirectory'] })

      let pathSel = pathArray.filePaths

      dest_dir.innerHTML = pathSel
      pathInfo.DestDirectory = pathSel.toString()
      myConsole.log(TAG, 'btn_browse_dest_dir/pathInfo:', pathInfo)
    } catch (err) {
      alert(err)
    }
  });


  // To validate From & To dates for Mining, this method will be called once 'DateRange' radiobutton selected.
  function validateMiningFromAndToDates(from, to) {

    let errMsg = 'TO date must be greater than FROM date'

    if (from == '' || from == undefined) {
      alert('Please Select Start Date')
      return false
    } else if (to == '' || to == undefined) {
      alert('Please Select End Date')
      return false
    }

    let arr_splitted_from_date = from.split("-")
    let arr_splitted_to_date = to.split("-")

    let from_year = arr_splitted_from_date[0];
    let from_month = arr_splitted_from_date[1];
    let from_day = arr_splitted_from_date[2];

    let to_year = arr_splitted_to_date[0];
    let to_month = arr_splitted_to_date[1];
    let to_day = arr_splitted_to_date[2];

    if (from_year > to_year) {
      alert(errMsg)
      return false
    } else if (from_year == to_year) {
      if (from_month > to_month) {
        alert(errMsg)
        return false
      } else if (from_month == to_month) {
        if (from_day >= to_day) {
          alert(errMsg)
          return false
        }
      }
    }

    return true
  }
  // Set From & To Dates
  function setMiningFromAndToDates(from, to) {
    dictDatesForMining.from = from
    dictDatesForMining.to = to
  }
  // Radio button 1 selection
  radio_btn_choice1.addEventListener('click', async () => {

    div_dateselection.style.display = 'none'

    // Setting from & to dates in dictionary with empty
    dictDatesForMining.from = ""
    dictDatesForMining.to = ""
  })

  // Radio button 2 selection
  radio_btn_choice2.addEventListener('click', async () => {
    div_dateselection.style.display = 'block'
  })

  // Start Mining
  btn_start_mining.addEventListener('click', async () => {
    
    try {
      // myConsole.log(TAG, 'btn_start_mining/pathInfo:', pathInfo)
      if (pathInfo.gitDirectory == '') {
        alert('Please Select Git Directory')
      } else if (pathInfo.DestDirectory == '') {
        alert('Please Select Destination Directory')
      } else {
        // Checking whether Date Selection for Mining Selected or not, Managing Dates here only. Not by clicking Radio buttons, Because that is useless
        if (isDateRangeSelected()) {
          let startDate = input_start_date.value
          let endDate = input_end_date.value
          // Validating Date
          if(validateMiningFromAndToDates(startDate, endDate)) {
            setMiningFromAndToDates(startDate, endDate)
          } else {
            return
          }
        } else {
          setMiningFromAndToDates("All", "All")
        }

        let reponame = path.basename(pathInfo.gitDirectory) + '.git.csv'

        // Checking if "DevRanker" directory available, if not available then creating it.
        initAndCreateDevRankerDirectoryIfNotExisting()

        pathInfo.output_file_name = path.join(pathInfo.devranker_dir, reponame)

        myConsole.log(TAG, 'btn_start_mining::AfterUpdate::', pathInfo, '\nDateRange:',dictDatesForMining)

        // Communicate with Python
        let options = {
          mode: 'text',
          args: ['start_mining', pathInfo.gitDirectory, pathInfo.devranker_dir, pathInfo.output_file_name, dictDatesForMining.from, dictDatesForMining.to]
        };

        progress_element.value = "0"
        // Showing Progressbar
        show_progress.style.display = "block"

        let pyshell = new PythonShell(pythonFileName, options);

        pyshell.on('message', function (message) {

          myConsole.log("btn_start_mining/PhthonShell-start_mining::", message)

          try {

            // myConsole.log("btn_start_mining/PhthonShell-start_mining::", message)

            let data_parsed = JSON.parse(message)


            if (data_parsed.msg == 'Done') {

              alert("Mining is done and File location is \n\n" + pathInfo.output_file_name)
              // Hiding Porgressbar
              show_progress.style.display = "none"
              progress_display.innerHTML = ""

              data_file_location.innerHTML = pathInfo.output_file_name

              update_STEP_1_StatusBarColor()

            } else if(data_parsed.msg == 'no_commits') {
              alert("No commits available for selected Date Range")
              show_progress.style.display = "none"
              progress_display.innerHTML = ""
            } else if (data_parsed.msg == 'Progress') {

              progress_element.max = data_parsed.tc
              progress_element.value = data_parsed.cc

              progress_display.innerHTML = data_parsed.cc + " / " + data_parsed.tc
              
              myConsole.log(data_parsed.cc, " / ", data_parsed.tc)

            } else {
              alert(message)
            }
          } catch (err) {
            alert(err)
          }
        });
      }
    } catch (err) {
      myConsole("Start Mining exception:", err)
      alert("btn_start_mining:" + err)
    }
  });

  // Anonymize
  btn_anonymize.addEventListener('click', (event) => {
    try {
      if (pathInfo.DestDirectory == '') {
        alert('Please Choose Destination Directory')
        return
      } else if (pathInfo.output_file_name == '') {
        alert('There is no Mined File to Anonymize')
        return
      }

      initAndCreateDevRankerDirectoryIfNotExisting()
      let reponame = path.basename(pathInfo.output_file_name) // this one had .git.csv already

      pathInfo.anonymized_file_path = path.join(pathInfo.devranker_dir, 'anonymized_' + reponame)
      pathInfo.email_hash_dict_file_path = path.join(pathInfo.devranker_dir, reponame + '.email_dict.pickle')
      let options = {
        mode: 'text',
        args: ['anonymize', pathInfo.output_file_name, pathInfo.email_hash_dict_file_path, pathInfo.anonymized_file_path]
      };

      myConsole.log(TAG, 'btn_anonymize::', pathInfo)

      PythonShell.run(pythonFileName, options, function (err, results) {

        try {
          myConsole.log("PythonShell/anonymize/success-response::", results)
          myConsole.log("PythonShell/anonymize/error-response::", err)

          if (results != null) {

            let data = results[0]

            if (data == 'Done') {
              alert('Anonymize is done. \n\nAnonymize File location:\n' + pathInfo.anonymized_file_path +
                '\n\nAnonymize File Dictionary location:\n' + pathInfo.email_hash_dict_file_path)

              ann_file_location.innerHTML = pathInfo.anonymized_file_path
              ann_dict_located_at.innerHTML = pathInfo.email_hash_dict_file_path

            } else {
              alert(results)
            }
          } else {
            alert("PythonShell Anonymize Error::\n\n" + err)
          }
        } catch (err) {
          alert(err)
        }
      });
    } catch (err) {
      alert(err)
    }
  });

  // Get Predictions
  btn_get_predictions.addEventListener('click', (event) => {
   
    try {
      if (pathInfo.DestDirectory == '') {
        alert('Please Choose Destination Directory')
        return
      } else if (pathInfo.anonymized_file_path == '') {
        alert('Anonymized file Not Available to do Predictions')
        return
      }

      initAndCreateDevRankerDirectoryIfNotExisting()
      let reponame = path.basename(pathInfo.anonymized_file_path)

      apicall_getPredictionsFile(reponame)
    } catch (err) {
      alert(err)
    }
  });

  // De-Anonymize
  btn_de_ann.addEventListener('click', (event) => {
   
    try {
      if (pathInfo.DestDirectory == '') {
        alert('Please Choose Destination Directory')
        return
      } else if (pathInfo.predicted_file_path == '') {
        alert('Predictions File not available for De-Anonymize')
        return
      } else if (pathInfo.email_hash_dict_file_path == '') {
        alert('Email-Pickle File not available for De-Anonymize')
        return
      }

      initAndCreateDevRankerDirectoryIfNotExisting()
      let reponame = path.basename(pathInfo.predicted_file_path)

      if(!reponame.includes("_anonymized")) {
          // Ravi: Because i want to maintain following structure
          // "cpu_scores_anonymized_<repoName>.csv" - For Anonymized File name
          // "cpu_scores_de_anonymized_<repoName>.csv" - For De-Anonymized File name
          // So if there is no '_anonymized' in file name then i cant fulfil the requirement as user uploaded wrong file or renamed file which is not acceptable
          alert("Not a valid Anonymized file, Please upload valid File")
          return
      } 
      reponame = reponame.replace("_anonymized", "_de_anonymized")

      pathInfo.de_anonymized_file_path = path.join(pathInfo.devranker_dir, reponame)
      let options = {
        mode: 'text',
        args: ['de_anonymize',
          pathInfo.predicted_file_path,
          pathInfo.email_hash_dict_file_path,
          pathInfo.de_anonymized_file_path
        ]
      };

      myConsole.log(TAG, 'de_anonymize::', pathInfo)

      PythonShell.run(pythonFileName, options, function (error_result, results) {

        try {

          myConsole.log("PythonShell/de_anonymize::", 'results::', results, 'error response::', error_result)

          if (results != null) {

            let data = results[0]

            myConsole.log("de_anonymize::", results)

            if (data == 'Done') {

              alert('De Anonymizing is done. \n\nFile location is:\n' + pathInfo.de_anonymized_file_path)

              de_ann_pre_file.innerHTML = pathInfo.de_anonymized_file_path

              storePathInfoInMainJs()

              update_STEP_3_StatusBarColor()

            } else if (data == 'exc') {
              alert(results[1])
            }
          } else {
            alert(error_result)
          }
        } catch (err) {
          alert(err)
        }
      });
    } catch (err) {
      alert(err)
    }
  });

  // Data File Location at
  btn_dfla.addEventListener('click', async (event) => {
    try {
      const pathArray = await remote.dialog.showOpenDialog({ properties: ['openFile'] })
      let pathSel = pathArray.filePaths
      data_file_location.innerHTML = pathSel
      pathInfo.output_file_name = pathSel.toString()
    } catch (err) {
      alert(err)
    }
  });

  // Anonymization File Location at
  btn_afla.addEventListener('click', async (event) => {
    try {
      const pathArray = await remote.dialog.showOpenDialog({ properties: ['openFile'] })
      let pathSel = pathArray.filePaths
      ann_file_location.innerHTML = pathSel
      pathInfo.anonymized_file_path = pathSel.toString()
    } catch (err) {
      alert(err)
    }
  });
  // Anonymization Dictionary Located at
  btn_adla.addEventListener('click', async (event) => {
    try {
      const pathArray = await remote.dialog.showOpenDialog({ properties: ['openFile'] })
      let pathSel = pathArray.filePaths
      ann_dict_located_at.innerHTML = pathSel
      pathInfo.email_hash_dict_file_path = pathSel.toString()
    } catch (err) {
      alert(err)
    }
  });
  // Anonymization Predictions File
  btn_apf.addEventListener('click', async (event) => {
    try {
      const pathArray = await remote.dialog.showOpenDialog({ properties: ['openFile'] })
      let pathSel = pathArray.filePaths
      ann_predictions_file.innerHTML = pathSel
      pathInfo.predicted_file_path = pathSel.toString()
    } catch (err) {
      alert(err)
    }
  });

  // Change Graph File Location
  btn_graph_path.addEventListener('click', async (event) => {
    try {
      const pathArray = await remote.dialog.showOpenDialog({ properties: ['openFile'] })
      let pathSel = pathArray.filePaths
      de_ann_pre_file.innerHTML = pathSel
      pathInfo.de_anonymized_file_path = pathSel.toString()
      storePathInfoInMainJs()
    } catch (err) {
      alert(err)
    }
  });


  // Show Charts
  btn_show_charts.addEventListener('click', (event) => {
   
    if (pathInfo.de_anonymized_file_path == '') {
      alert('Please Choose De-Anonymized File to see Charts')
      return
    }

    update_STEP_4_StatusBarColor()
    // show_charts_href.click()
    remote.getCurrentWindow().loadFile('./html/graph.html')
  });

} catch (err) {
  alert(err)
  myConsole("Global exception:", err)
}

// Packaging Ref:
// https://coursetro.com/posts/code/124/Electron-App-Deployment-Tutorial