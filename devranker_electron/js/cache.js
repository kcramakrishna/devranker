
  // ###########################################################
  // ##################   Setters & Getters   ##################
  // ###########################################################  
  var devranker_dir = ""
  var output_file_name = ""
  var gitDirectory = ""
  var DestDirectory = ""

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
