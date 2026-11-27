import React from 'react';
import { registerRootComponent } from 'expo';

import App from './App';
import { ErrorBoundary } from './src/ErrorBoundary';
import { installErrorReporting } from './src/errors';

installErrorReporting();

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
function Root() {
  return React.createElement(ErrorBoundary, null, React.createElement(App));
}
registerRootComponent(Root);
