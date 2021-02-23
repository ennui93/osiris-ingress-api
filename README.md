# osiris-ingress-api <!-- omit in toc -->
- [Data application registration](#data-application-registration)
  - [Prerequisites](#prerequisites)
  - [Steps](#steps)
    - [Create an App Registration](#create-an-app-registration)
    - [Create a Service Principal and credentials](#create-a-service-principal-and-credentials)
    - [Grant access to the dataset](#grant-access-to-the-dataset)
- [Development](#development)
  - [tox](#tox)
  - [Commands](#commands)
    - [Linting](#linting)
    - [Tests](#tests)

## Data application registration

An App Registration with credentials are required to upload data to the Data Platform through the Osiris Ingress API.

### Prerequisites

* The dataset has been created through [the Data Platform](https://dataplatform.energinet.dk/).
* The Azure CLI is installed on your workstation

### Steps
Login with the Azure CLI with the following command:

``` bash
az login
```

You can also specify a username and password with:

``` bash
az login -u <username> -p <password>
```

#### Create an App Registration
The App Registration serves as a registration of trust for your application (or data publishing service) towards the Microsoft Identity Platform (allowing authentication).

This is the "identity" of your application.
Note that an App Registration is globally unique.

Run the following command:
``` bash
az ad app create --display-name "<YOUR APP NAME>"
```

The application name should be descriptive correlate to the application/service you intend to upload data with.

Take note of the `appId` GUID in the returned object.


#### Create a Service Principal and credentials
The Service Principal and credentials are what enables authorization to the Data Platform.

Create a Service Principal using the `appId` GUID from when creating the App Registration:
``` bash
az ad sp create --id "<appID>"
```

Then create a credential for the App Registration:

``` bash
az ad app credential reset --id "365f9c66-b4dc-47eb-b311-84c592c441cb"
```

**NOTE:** Save the output somewhere secure. The credentials you receive are required to authenticate with the Osiris Ingress API.


#### Grant access to the dataset
The application must be granted read- and write-access to the dataset on [the Data Platform](https://dataplatform.energinet.dk/).

Add the application you created earlier, using the `<YOUR APP NAME>` name, to the read- and write-access lists.


## Development

### tox

Development for this project relies on [tox](https://tox.readthedocs.io/).

Make sure to have it installed.

### Commands

If you want to run all commands in tox.ini

```sh
$ tox
```

#### Linting

You can also run a single linter specified in tox.ini. For example:

```sh
$ tox -e flake8
```


#### Tests

Run unit tests.

```sh
$ tox -e py3
```

Run a specific testcase.

```sh
tox -e py3 -- -x tests/test_main.py
```
