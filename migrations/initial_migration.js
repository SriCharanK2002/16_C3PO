const Migrations =Artifacts.require("hi");
module.exports =function (deployer){
    deployer.deploy(Migrations);
};