(function(){
    angular
        .module("turtleFacts")
        .controller("resultsCtrl", ResultsController);

    ResultsController.$inject = ['quizMetrics', 'DataService','$http'];

    function ResultsController(quizMetrics, DataService,$http){
        var vm = this;

        vm.quizMetrics = quizMetrics; 
        vm.dataService = DataService;
        vm.getAnswerClass = getAnswerClass;
        vm.setActiveQuestion = setActiveQuestion; 
        vm.reset = reset; 
        vm.calculatePerc = calculatePerc; 
        vm.activeQuestion = 0;
        vm.postResults=false;

        function calculatePerc(){
            console.log("--------------------------init ");
            if(quizMetrics.resultsActive==true && vm.postResults==false)
            {
                vm.postResults=true
                var percent=quizMetrics.numCorrect / DataService.quizQuestions.length * 100;
            var postData = {
                percentage: percent
            };
            var url = 'http://127.0.0.1:5056/store-quiz-result';

            $http.post(url, postData)
                .then(function(response) {
                    console.log('Data sent successfully:', response.data);
                    console.log("-------------------------------------success");
                }, function(error) {
                    console.error('Error sending data:', error);
                    console.log("-------------------------------------erroe");
                });
                
            }

            return quizMetrics.numCorrect / DataService.quizQuestions.length * 100;
        }

        function setActiveQuestion(index){

            vm.activeQuestion = index;
        }

        function getAnswerClass(index){
            if(index === quizMetrics.correctAnswers[vm.activeQuestion]){
                return "bg-success";
            }else if(index === DataService.quizQuestions[vm.activeQuestion].selected){
                return "bg-danger";
            }
        }

        function reset(){
            quizMetrics.changeState("results", false);
            quizMetrics.numCorrect = 0;

            for(var i = 0; i < DataService.quizQuestions.length; i++){
                var data = DataService.quizQuestions[i]; 

                data.selected = null;
                data.correct = null;
            }
        }

    }

})();
