window.config = {
  routerBasename: '/viewer', showStudyList: true, extensions: [], modes: [],
  defaultDataSourceName: 'kauvery',
  dataSources: [{namespace: '@ohif/extension-default.dataSourcesModule.dicomweb', sourceName: 'kauvery',
    configuration: {friendlyName: 'Public imaging demonstration', name: 'kauvery',
      wadoUriRoot: '/dicomweb', qidoRoot: '/dicomweb', wadoRoot: '/dicomweb',
      qidoSupportsIncludeField: true, imageRendering: 'wadors', thumbnailRendering: 'wadors',
      enableStudyLazyLoad: true, supportsFuzzyMatching: false, supportsWildcard: true}}]
};
