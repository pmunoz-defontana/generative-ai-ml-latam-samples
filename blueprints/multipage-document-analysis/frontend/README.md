# Base React App

This repository contains a base web application. It uses [Vite](https://vitejs.dev/) + [React](https://react.dev/). To deploy you will run a basic CDK stack using [Amazon S3](https://aws.amazon.com/s3/) and [Amazon Cloudfront](https://aws.amazon.com/cloudfront/) with [AWS WAF](https://aws.amazon.com/waf/) for security.

## Requirements

In order to run and deploy this project, you need to have installed:

- AWS CLI. Refer to [Installing the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
- AWS Credentials configured in your environment. Refer to
  [Configuration and credential file settings](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- Node >= 18.x.x
- AWS CDK. Refer to [Getting started with the AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)

You also need to have the proper backend stack for your prototype deployed into your account, as well as a valid user configured in [Amazon Cognito](https://aws.amazon.com/cognito/).

Make sure to deploy the frontend using the same configuration option as your backend.

---

## Developing and running locally

### Configuring your environment

In a terminal, run:

```shell
$ cd webapp/
```

Inside the `webapp/` folder, create a file named `.env`. Copy the environment displayed below and replace the property values with the outputs from your deployed backend stack.

```properties
VITE_AWS_REGION="<<Stack-MultipageDocumentAnalysis.REGION_NAME>>"
VITE_COGNITO_USER_POOL_ID="<<Stack-MultipageDocumentAnalysis.COGNITO_USER_POOL_ID>>"
VITE_COGNITO_USER_POOL_CLIENT_ID="<<Stack-MultipageDocumentAnalysis.COGNITO_USER_POOL_CLIENT_ID>>"
VITE_COGNITO_IDENTITY_POOL_ID="<<Stack-MultipageDocumentAnalysis.COGNITO_IDENTITY_POOL_ID>>"
VITE_API_GATEWAY_REST_API_ENDPOINT="<<Stack-MultipageDocumentAnalysis.API_GATEWAY_REST_API_ENDPOINT>>"
VITE_API_NAME="<API_NAME>"
VITE_APP_NAME="PACE Sample Project"
```

**Note:** The values for the inputs in-between < > signs are user defined inputs while the ones in-between << >> are part of this stack's outputs.

### Developing with dev mode

From the `webapp/` folder, you can run the following command in a terminal to run the app in development mode:

```shell
$ npm i
$ npm run dev
```

Open [http://localhost:5173/](http://localhost:5173/) to view it in your browser.

The page will reload when you make changes. You may also see any lint errors in the console.

### Developing with watch and hot reloading

In one terminal window, run:

```shell
$ npm run watch
```

In another window, run:

```shell
$ npm run preview
```

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules. It builds the app for production to the `dist` folder. It correctly bundles React in production mode and optimizes the build for the best performance.