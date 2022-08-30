function ViewModel() {
    var self = this;

    self.responseValues = new ResponseValues();

    self.submitForm = function(group_id, student_id, myObservable, myVisible) {
        var fd = new FormData();
        fd.append("student", parseInt(student_id));
        fd.append("group", parseInt(group_id));
        fd.append("nota", parseFloat(myObservable()));
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
        return $.ajax('/teacher/upload-score/', {
            data: fd,
            type: "post",
            processData: false,
            contentType: false,
            success: function(response){
                myVisible(false);
            }
        });
    }
}
var vm = new ViewModel();