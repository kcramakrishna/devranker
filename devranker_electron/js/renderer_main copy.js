try {
  // Logs from Node.js(console.log wont work in renderer.js as this is not associated with main process, but from Html Script Tag)  
  var nodeConsole = require('console');
  var { PythonShell } = require('python-shell');
  var myConsole = new nodeConsole.Console(process.stdout, process.stderr);
  const { ipcRenderer } = require('electron')
  const { remote } = require('electron')

  var TAG = 'renderer_main.js::'
  // to replace os.path.join in python
  var path = require('path');
  // Variables for python paths


  // ###########################################################
  // ##################   Setters & Getters   ##################
  // ###########################################################  
  var devranker_dir = ""
  var output_file_name = ""
  var gitDirectory = ""
  var DestDirectory = ""


  var btnBrowse = document.getElementById("btn_browse_cln_repo");

  // // devranker_dir
  function set_devranker_dir(value) {
    this.devranker_dir = value;
  }

  function get_devranker_dir() {
    return this.devranker_dir;
  }


  function get_git_directory_path() {
    return this.gitDirectory
  }

  // repo Name
  function get_repo_name() {
    return path.basename(this.get_git_directory_path())
  }


  // '.git.csv'
  function get_target_repo_raw_data_file_name() {
    return this.get_repo_name() + '.git.csv'
  }


  // output_file_name
  function set_output_file_path(value) {
    this.output_file_name = path.join(this.get_devranker_dir(), this.get_target_repo_raw_data_file_name())
  }


  //  gitDirectory
  function set_git_directory_path(path) {
    this.gitDirectory = path
  }

  function get_git_directory_path() {
    return this.gitDirectory;
  }

  function devranker_dir() {
    return this.devranker_dir;
  }

  function get_output_file_path() {
    return this.output_file_name;
  }

  function get_target_repo_raw_data_file_name() {
    return this.get_repo_name() + '.git.csv';
  }

  // DestDirectory
  function set_dest_directory_path(path) {
    this.DestDirectory = path
  }

  function get_dest_directory_path() {
    return this.DestDirectory
  }

  //  repo Name
  function get_repo_name() {
    return path.basename(this.get_git_directory_path())
  }

  //  anonymized
  function get_anonymized_file_path() {
    // return get_devranker_dir() + '/anonymized_' + get_target_repo_raw_data_file_name()
    return path.join(this.get_devranker_dir(), 'anonymized_' + this.get_target_repo_raw_data_file_name())
  }

  //  anonymized dict
  function get_email_hash_dict_file_path() {
    return this.get_output_file_path() + '.email_dict.pickle'
  }

  // predictions dir
  function get_predictions_directory_path() {
    return this.get_devranker_dir()
    //  return os.path.join(get_dest_directory_path(), 'predictions')
  }

  function get_anonymized_predictions_file_path() {
    return path.join(this.get_devranker_dir(), 'scores_anonymized_elasticray.git.csv')
  }

  function get_dev_scores_voice_data_file_path() {
    return path.join(this.get_devranker_dir(), 'dev_scores_voice-data-backend.git.csv')
  }

  // ##########################################################





  // ***********************************************
  // **************** COMMUNICATION ****************
  // ***********************************************
  // ASYNCHRONOUS - RECEIVER
  ipcRenderer.on('asynchronous-testing-reply', (event, arg) => {
    console.log(arg)
    dest_dir.innerHTML = arg
  })

  // SYNCHRONOUS - SENDER & RECEIVER(Immediate callback)
  // synchronous_callback = ipcRenderer.sendSync('synchronous-testing', 'sync ping')
  // dest_dir.innerHTML = synchronous_callback


  // ASYNCHRONOUS - SENDER
  // ipcRenderer.send('asynchronous-testing', 'Select Folder')





  // ##########################################################
  // ##################   Setters & Getters   ##################
  // ##########################################################
  // OnClick: Clone Repository
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

      PythonShell.run('./py/pyt.py', options, function (err, results) {

        myConsole.log(TAG, 'error:', err, 'resp_result:', results)

        let data_parsed = JSON.parse(results[0])

        if (data_parsed.status == true) {
          gitDirectory = pathSel
        } else {
          alert(pathSel + '\n\n' + data_parsed.msg)
          cln_repo.innerHTML = ''
        }

      });
    } catch (err) {
      alert(err)
    }
  });





  // OnClick: Browse Destination Directory
  btn_browse_dest_dir.addEventListener('click', async (event) => {

    try {
      const pathArray = await remote.dialog.showOpenDialog({ properties: ['openDirectory'] })

      let pathSel = pathArray.filePaths

      dest_dir.innerHTML = pathSel
      DestDirectory = pathSel
      // myConsole.log(TAG, 'btn_browse_dest_dir/pathInfo:')
    } catch (err) {
      alert(err)
    }
  });


  // OnClick: Start Mining
  btn_start_mining.addEventListener('click', async (event) => {

    try {

      // myConsole.log(TAG, 'btn_start_mining/pathInfo:', pathInfo)

      if (gitDirectory === '') {
        alert('Please Select Git Directory')
      } else if (DestDirectory === '') {
        alert('Please Select Destination Directory')
      } else {


        myConsole.log("lkdjf")



        // Communicate with Python
        // let options = {
        //   mode: 'text',
        //   args: ['start_mining', pathInfo.get_git_directory_path, pathInfo.get_devranker_dir, pathInfo.get_output_file_path]
        // };

        // PythonShell.run('./py/pyt.py', options, function (err, results) {

        //   myConsole.log(TAG, 'error:', err, 'resp_result:', results)

        //   let data_parsed = JSON.parse(results[0])

        //   if (data_parsed.status == true) {
        //     pathInfo.gitDirectory = pathSel
        //     myConsole.log(TAG, 'gitDirectory:', pathInfo.gitDirectory)
        //   } else {
        //     alert(pathSel + '\n\n' + data_parsed.msg)
        //     cln_repo.innerHTML = ''
        //   }
        // });
      }




    } catch (err) {
      myConsole("Start Mining exception:", err)
      alert(err)
    }
  });

} catch (err) {
  myConsole("Global exception:", err)
  alert(err)
}