// Inter Process Communication(JS to Python Communication) ways - child_process, PythonShell & Flask. We used 'PythonShell'
// Ref: https://www.ahmedbouchefra.com/connect-python-3-electron-nodejs-build-desktop-apps/

try {
  // Logs from Node.js(console.log wont work in renderer.js as this is not associated with main process, but from Html Script Tag)  
  var nodeConsole = require('console');
  const { type } = require('os');
  const { ipcRenderer } = require('electron')
  var myConsole = new nodeConsole.Console(process.stdout, process.stderr);
  let pythonFileName = './py/devranker_functions.py'


  // Initializing Selector(Dropdown) related variables
  let list_authors = []
  let list_authors_data = []
  let list_languates = ["Java", "Python", "React"]
  let list_selected_authors = ['All']

  // Initializing Graph related variables
  let list_x_axis_months = ["Jan", "Feb", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
  let list_graph_dataset = []
  let list_sum_of_mods = []




  // Instances for widgets
  var ctx_for_linechart = document.getElementById("chart_line_area");
  var ctx_for_piechart = document.getElementById("chart_pie_area");


  // Setting default Year & Month to From & To Date pickers
  date_today = new Date()
  myConsole.log(new Date().getFullYear(), new Date().getMonth())
  input_from_month_and_year.defaultValue = date_today.getFullYear() - 1 + "-" + date_today.getUTCMonth() + 1;
  input_to_month_and_year.defaultValue = date_today.getFullYear() + "-" + date_today.getMonth() + 1;

  // By using 'PythonShell'(which is using IPC), communicating with Python file i.e, 'graph.py'
  function getDataFromPython(dev_predictions_file_path) {

    var { PythonShell } = require('python-shell');

    let options = {
      mode: 'text',
      args: ['get_csv_data', dev_predictions_file_path]
    };

    PythonShell.run(pythonFileName, options, function (err, results) {
      try {
        if (err) throw err;
        // results is an array consisting of messages collected during execution
        // res = JSON.stringify(results[0])
        // res = JSON.parse(results[0]) 
        let data_parsed = JSON.parse(results[0])

        list_authors = Object.keys(data_parsed)
        list_authors_data = Object.values(data_parsed)

        // myConsole.log('\n\nparsed data ::', data_parsed["abdon.pijpelink@elastic.co"])
        myConsole.log('\n\nparsed data ::', data_parsed)
        myConsole.log('\n\nauthors ::', list_authors)
        myConsole.log('\n\nlist_authors_data ::', list_authors_data)

        setSelectors()

      } catch (err) {
        alert("Exception while reading below file \n" + dev_predictions_file_path + "\n\n" + err)
      }
    });
  }

  // Loading Line Graph with 'Chart.js'
  function loadLineGraph() {
    try {
      ctx_for_piechart.style.display = "none"
      ctx_for_linechart.style.display = 'block'

      new Chart(chart_line_area, {
        type: "line",
        data: {
          labels: list_x_axis_months,
          datasets: list_graph_dataset,
        },
        options: {
          scales: {
            xAxes: [{
              display: true,
              scaleLabel: {
                display: true,
                labelString: 'Month'
              }
            }],
            yAxes: [{
              display: true,
              scaleLabel: {
                display: true,
                labelString: 'Mod Score'
              },
              ticks: {
                beginAtZero: true,
              },
            }]
          },
          elements: {
            point: {
              pointStyle: 'rectRot'
            }
          }
        },
      });

    } catch (err) {
      alert(err)
    }
  }

  // Loading Pie Chart Graph
  function loadPieGraph() {


    myConsole.log('\n\nLoading pie Chart::\n')

    try {

      let list_mods_sum = []

      // Preparing Mods Total for Authors
      for (x in list_graph_dataset) {

        myConsole.log('\n\n\n\nAuthor:, ', list_authors[x], "::\n", list_graph_dataset[x])
        myConsole.log('ModScores:', "::\n", list_graph_dataset[x].data)

        let temp = 0

        for (y in list_graph_dataset[x].data) {
          temp = temp + parseInt(list_graph_dataset[x].data[y])
        }

        list_mods_sum.push("" + temp)

        temp = 0

        myConsole.log('Mods Total for Author, ', list_authors[x], " is::", temp) // , "\n\nPieChartList is::", list_mods_sum)
      }

      // Preparing Background colors for each Mod Total of Author
      list_bg_colors = []
      for (x in list_authors) {
        var rgbVals = randomRGB();
        let bg_color = "rgb(" + rgbVals[0] + ", " + rgbVals[1] + ", " + rgbVals[2] + ")"
        list_bg_colors.push(bg_color)
      }

      // Managing Visibility of canvas of line & pie charts
      myConsole.log('\n\n\n Pie Chart Data after Added Mod Scores for idividual Authores is::', list_mods_sum)
      ctx_for_linechart.style.display = "none"
      ctx_for_piechart.style.display = 'block'

      // Preparing Config
      var config = {
        type: 'pie',
        data: {
          datasets: [{
            data: list_mods_sum,
            backgroundColor: list_bg_colors,
            label: 'Dataset 1'
          }],
          labels: list_authors
        },
        options: {
          responsive: true
        }
      };

      new Chart(chart_pie_area, config);

    } catch (err) {
      alert(err)
    }
  }

  // Preparing Idividual Author's Data to add for Graph Dataset i.e, 'list_graph_dataset'
  // 'name' is Label Name & 'array_mods' is y-Axis values for 12 months(For X-Axis)
  function get_graph_dataset_obj(name, array_mods) {

    var rgbVals = randomRGB();
    var rgbVals_2 = randomRGB();

    let bg_color = "rgb(" + rgbVals[0] + ", " + rgbVals[1] + ", " + rgbVals[2] + ")"
    let b_color = "rgb(" + rgbVals_2[0] + ", " + rgbVals_2[1] + ", " + rgbVals_2[2] + ")"

    return {
      label: name,
      fill: false,
      data: array_mods,
      backgroundColor: bg_color,
      borderColor: bg_color,
      pointRadius: 10,
      pointHoverRadius: 15,
      borderWidth: 1,
    }
  }

  // To Generate Random RGB Values, which is required to generate Random Colors for Graph Line Background & Border
  function randomRGB() {
    var red = randomNum();
    var green = randomNum();
    var blue = randomNum();
    return [red, green, blue];
  }

  function randomNum() {
    return Math.floor(Math.random() * 256);
  }

  // Appending data to Selectors(Dropdowns). i.e, Author Email & Language
  function setSelectors() {

    for (var x in list_authors) {
      select_emails.options[select_emails.options.length] = new Option(list_authors[x], x);
    }

    for (var x in list_languates) {
      select_languages.options[select_languages.options.length] = new Option(list_languates[x], x);
    }

    // On Author Email Selected
    select_emails.onchange = function () {

      list_selected_authors = [];

      for (var option of select_emails.options) {
        if (option.selected) {
          list_selected_authors.push(option.value);
        }
      }
      myConsole.log('Selected Author Indexes::', list_selected_authors)
    }

    // On Language Selected
    select_languages.onchange = function () {
      myConsole.log('Selected Language Index::', this.value)
    }
  }

  function prepareGraphData(isLineGraph) {

    try {

      let arr_splitted_from_date = (input_from_month_and_year.value).split("-")
      let arr_splitted_to_date = (input_to_month_and_year.value).split("-")

      let from_year = arr_splitted_from_date[0];
      let from_month = arr_splitted_from_date[1];

      let to_year = arr_splitted_to_date[0];
      let to_month = arr_splitted_to_date[1];


      // Validating Month & Year
      // (0 - Same Year) || (-1 - Correct Diff, From month > To Month)-> 
      // parseInt - To convert String into Integer
      if ((parseInt(from_year) - parseInt(to_year) == 0) || (parseInt(from_year) - parseInt(to_year) == -1 && parseInt(from_month) >= parseInt(to_month))) {
        list_graph_dataset = []
      } else {
        alert("From & To Dates Interval must be 12 months")
        return
      }
      // myConsole.log("From & To ::", from_year, from_month, to_year, to_month)

      for (x in list_authors) {

        if (list_selected_authors.includes(x) || list_selected_authors.includes('All')) {

          let list_mods_of_all_months = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

          let auth_data = list_authors_data[x]

          // Separating keys & values of 'list_authors_data'
          let list_keys = Object.keys(auth_data)
          let list_values = Object.values(auth_data)


          for (y in list_keys) {
            let date = new Date(list_keys[y])
            let data_month = date.getUTCMonth() + 1
            let data_year = date.getUTCFullYear()

            // myConsole.log(list_authors[x], "SubDirectoryIndex::", y, "::", data_year, data_month)

            // Validating with FROM & TO month-year
            if (from_year <= data_year && to_year >= data_year) {

              // Updating mod score by adding it to current mod for that month
              // Existing value + Current value, -1 is for index

              // myConsole.log('month is :', data_month, "Its mod Value is:", list_values[y], "Present Mod value of month ", list_mods_of_all_months)

              let updated_mod_value = list_mods_of_all_months[data_month - 1] + list_values[y]

              // Updating existing value in list 'list_mods_of_all_months' by considering index as 'data_month'
              list_mods_of_all_months.splice(data_month - 1, 1, updated_mod_value)

              // myConsole.log(list_mods_of_all_months)
            }
          }
          myConsole.log(list_authors[x], "ModsList::", list_mods_of_all_months)
          list_graph_dataset.push(get_graph_dataset_obj(list_authors[x], list_mods_of_all_months))
        }
      }
    } catch (err) {
      myConsole.log("btn_clicked::exception::", err)
      alert(err)
    }

    myConsole.log("list_graph_dataset::", list_graph_dataset)

    // Till now prepared Dataset, Loading Graph now
    if (isLineGraph) {
      loadLineGraph()
    } else {
      loadPieGraph()
    }
  }

  // On Clicking 'Load Line Chart' button
  btn_load_line.addEventListener('click', () => {
    prepareGraphData(true)
  });

  // On Clicking 'Load Pie Chart' button
  btn_load_pie.addEventListener('click', () => {
    prepareGraphData(false)
  });


  btn_back.addEventListener('click', () => {
    const { remote } = require('electron')
    // remote.getCurrentWindow().back()
    // window.history.back();
    remote.getCurrentWindow().loadFile('./html/home.html')
    // history.go(-1)
  })


  let pathInfo = ipcRenderer.sendSync('synchronous-getPathInfo', 'get pathInfo')

  myConsole.log('\n\nrenderer_graph.js::synchronous-getPathInfo::', pathInfo)

  if (pathInfo != undefined) {
    getDataFromPython(pathInfo.de_anonymized_file_path)
  } else {
    alert('Unable to fetch De-Anonymized file path')
  }
} catch (err) {
  alert(err)
}