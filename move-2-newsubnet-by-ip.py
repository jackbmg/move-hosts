#!/usr/bin/env python
import sys, socket
from iptools.client import Client, ClientError

if len(sys.argv) != 3:
	sys.exit("usage: movetonewsubnet.py new-subnet-name current-ip-address")
#hard code current iptools web site here
iptools_server=raw_input('IPtools server name: ')
token=raw_input('Please enter your api token: ')
iptools_server=iptools_server.strip()
token=token.strip()
# Create an API client with input from command line:
c = Client(token, host=iptools_server)

def validate_iptools_server(hostname):
    try:
        socket.gethostbyname(hostname)
        return 1
    except socket.error:
        return 0

def validate_subnet(subnet):
	found_subnet = ''
	found = False
	print 'Verifying subnet ...'
	for i in c.ipv4subnets.all():
		if i['name']==subnet:
			found = True
			found_subnet=c.ipv4subnets.get(i['id'])
	if found: 
		return found_subnet
	else: 
		print 'FAIL: subnet not found.. exiting program...'
		sys.exit()

def validate_available_ips(subnet):
	#verify that there are available addresses in the new subnet
	print 'Verifying if ' + str(subnet['name']) + ' has an available address ...'
	if subnet['available'] > 0:
		print '%s has %i available addresses\n\n' % (subnet['name'], subnet['available'])
	else:
		print 'FAIL: %s has %i available addresses... Exiting program...' % (subnet['name'], subnet['available'])
		sys.exit()


def move_current_ip(ip,subnet):
	current_ip = c.ipv4addresses.get(ip)
	if current_ip['status']=='A':
		print 'FAIL: IP ' + current_ip['address'] + ' is not currently assigned.. please check that you are using a valid IP...exiting program...'
		sys.exit() 
	elif current_ip['status']=='R':
		print 'FAIL: IP ' + current_ip['address'] + ' is currently reserved.. please check that you are using a valid IP...exiting program...'
		sys.exit()
	# add check for dhcp assigned address
	# capture the current hostname and domain
	current_hostname = current_ip['fqdn']['hostname']
	current_domainname = current_ip['fqdn']['domain']['name']
	print 'Moving ' + current_hostname + '.' + current_domainname + ' from ' + str(ip)
	# release the old one
	c.ipv4addresses.release(current_ip['id'])
	# assign to a new address
	new_address = c.ipv4addresses.request(c.ipv4subnets.available(subnet['id'])[0]['id'])
	# print new_address
	# ..and assign the old hostname and domain
	new_name = c.domainnames.create(new_address['id'], current_hostname, subnet['domains'][0]['id'])
	# print 'new_name: ' + str(new_name)
	print 'SUCCESS: host ' + str(new_name['hostname']) + '.' + str(new_name['domain']['name']) + ' is now assigned to ' + str(new_address['address'])
	return()

def main():
	mycurrentip=sys.argv[1]
	mysubnet=sys.argv[2]
	# verify that you can reach the iptools server
	if validate_iptools_server(iptools_server) == 0:
		print 'Error resolving iptools.swg.usma.ibm.com, are you on the IBM P9 Network?'
		sys.exit()
	# verify that your new subnet exists
	mynewsubnet = validate_subnet(mysubnet)
	if mynewsubnet:
		print mysubnet + ' found!\n'
	validate_available_ips(mynewsubnet)
	move_current_ip(mycurrentip, mynewsubnet)

if __name__=='__main__':
	main()
