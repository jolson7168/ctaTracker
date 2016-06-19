
provider "aws" {
    access_key = "${var.aws_access_key}"
    secret_key = "${var.aws_secret_key}"
    region = "${var.aws_region}"
}

resource "aws_security_group" "ctaTracker" {
  name = "ctaTracker-sg"
  description = "CTA Tracker Security Group"
  vpc_id = "${var.aws_vpc_id}"

  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = "0"
    to_port = "0"
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags {
    Name = "ctaTracker Node"
  }
}


resource "template_file" "salt_bootstrap_ctaTracker" {
    count    = "${var.ctaTracker_count}"
    template = "${file("salt_bootstrap_ctaTracker.tpl")}"

    vars {
        hostname = "${lookup(var.ctaTracker_hostnames, count.index)}"
        local_ip = "${lookup(var.ctaTracker_ips, count.index)}"
    }
}

resource "aws_instance" "ctaTracker" {

    count = "${var.ctaTracker_count}" 
    ami = "${var.aws_ubuntu_ami}"
    instance_type = "t2.micro"
    subnet_id = "${var.aws_subnet_id}"
    vpc_security_group_ids = ["${aws_security_group.ctaTracker.id}"]
    associate_public_ip_address = false
    private_ip = "${lookup(var.ctaTracker_ips, count.index)}"
    availability_zone = "${var.aws_availability_zone}"
    instance_initiated_shutdown_behavior = "stop"
    user_data = "${element(template_file.salt_bootstrap_ctaTracker.*.rendered, count.index)}"
    key_name = "${var.ctaTracker_rsa}"
    tags {
        Name = "CTA Tracker"
    } 
    root_block_device {  
        volume_size = 30
        volume_type = "gp2"
        delete_on_termination = true
    }

}
