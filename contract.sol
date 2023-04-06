pragma solidity ^0.8.0;
// SPDX-License-Identifier: GPL-3.0

contract ArtPlatform {
    
    address admin;
    uint user_count;
    
    struct User {
        uint id;
        string name;
        address payable wallet;
        // mapping (address => Project) i_own;
    }
    
    mapping (address => User) public users;
    mapping (uint => Project) public projects;
    mapping(address => uint[]) public userProjects;

    struct Project {
        uint id;
        string name;
        string description;
        address payable artist;
        address payable owner;
        uint price;
    }
    
    uint public projectCount;
    
    
    event ProjectCreated(uint id, string name, string description, address payable artist, uint price);
    event ProjectPurchased(uint id, string name, address payable buyer, uint price);
    
    constructor() {
        admin = msg.sender;
        projectCount = 0;
        user_count=0;
    }

    function register(string memory _name) public {
        require(users[msg.sender].wallet == address(0), "User already registered.");
        uint _id = user_count++;
        users[msg.sender] = User(_id, _name, payable(msg.sender));
    }
    
    function createProject(string memory _name, string memory _description, uint _price) public {
        require(users[msg.sender].wallet != address(0), "User not registered.");
        projectCount++;
        projects[projectCount] = Project(projectCount, _name, _description, payable(msg.sender),payable(msg.sender), _price);//making owner as artist
        emit ProjectCreated(projectCount, _name, _description, payable(msg.sender), _price);
        userProjects[msg.sender].push(projectCount);
    }
     
    function purchaseProject(uint _id) public payable {
        Project memory _project = projects[_id];
        require(_project.id > 0 && _project.id <= projectCount, "Invalid project id.");
        // require(!_project.isSold, "Project already sold.");
        require(msg.sender != _project.owner, "Can't purchase own project.");
        require(address(msg.sender).balance > _project.price, "Incorrect amount in vallet.");
        require(msg.value == _project.price, "Incorrect amount is being sent.");
        // msg.value      =_project.price;
        // _project.isSold = true;
        projects[_id] = _project;
        userProjects[msg.sender].push(_id);

        uint256[] storage values = userProjects[_project.owner];

        for (uint256 i = 0; i < values.length; i++) {
            if (values[i] == _id) {
                // Shift all elements after the one we want to remove
                for (uint256 j = i; j < values.length - 1; j++) {
                    values[j] = values[j+1];
                }
                // Remove the last element of the array
                values.pop();
                break;
            }
        }
        // userProjects[ _project.owner].delete(_id);
        
        
        // users[_project.artist].wallet.transfer(_project.price);
        // emit ProjectPurchased(_id, _project.name, payable(msg.sender), _project.price);
        _project.owner.transfer(msg.value);
        projects[_id].owner= payable(msg.sender);
        emit ProjectPurchased(_id, _project.name, payable(msg.sender), _project.price);

    }
    
    function returnProj(uint _id) public view returns(Project memory project1 ) {
        project1 = projects[_id];
    }
}
